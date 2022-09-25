from typing import (
    Any,
    AsyncGenerator,
    AsyncIterable,
    Awaitable,
    Dict,
    Generator,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import pymongo
from pymongo import MongoClient
from pymongo.client_session import ClientSession
from pymongo.collection import Collection
from pymongo.command_cursor import CommandCursor
from pymongo.database import Database

from odmantic.exceptions import DocumentNotFoundError, DuplicateKeyError
from odmantic.field import FieldProxy, ODMReference
from odmantic.index import ODMBaseIndex
from odmantic.model import Model
from odmantic.query import QueryExpression, SortExpression, and_
from odmantic.session import (
    AIOSession,
    AIOSessionBase,
    AIOTransaction,
    SyncSession,
    SyncSessionBase,
    SyncTransaction,
)
from odmantic.typing import lenient_issubclass

try:
    import motor
    from motor.motor_asyncio import (
        AsyncIOMotorClient,
        AsyncIOMotorClientSession,
        AsyncIOMotorCollection,
        AsyncIOMotorCursor,
        AsyncIOMotorDatabase,
    )
except ImportError:  # pragma: no cover
    motor = None


ModelType = TypeVar("ModelType", bound=Model)

SortExpressionType = Optional[Union[FieldProxy, Tuple[FieldProxy]]]

AIOSessionType = Union[AsyncIOMotorClientSession, AIOSession, AIOTransaction, None]
SyncSessionType = Union[ClientSession, SyncSession, SyncTransaction, None]


class BaseCursor(Generic[ModelType]):
    """This object has to be built from the [odmantic.engine.AIOEngine.find][] method.

    An AIOCursor object support multiple async operations:

      - **async for**: asynchronously iterate over the query results
      - **await** : when awaited it will return a list of the fetched models
    """

    def __init__(
        self,
        model: Type[ModelType],
        cursor: Union["AsyncIOMotorCursor", "CommandCursor"],
    ):
        self._model = model
        self._cursor = cursor
        self._results: Optional[List[ModelType]] = None

    def _parse_document(self, raw_doc: Dict) -> ModelType:
        instance = self._model.parse_doc(raw_doc)
        object.__setattr__(instance, "__fields_modified__", set())
        return instance


class AIOCursor(
    BaseCursor[ModelType], AsyncIterable[ModelType], Awaitable[List[ModelType]]
):
    """This object has to be built from the [odmantic.engine.AIOEngine.find][] method.

    An AIOCursor object support multiple async operations:

      - **async for**: asynchronously iterate over the query results
      - **await** : when awaited it will return a list of the fetched models
    """

    _cursor: "AsyncIOMotorCursor"

    def __init__(self, model: Type[ModelType], cursor: "AsyncIOMotorCursor"):
        super().__init__(model=model, cursor=cursor)

    def __await__(self) -> Generator[None, None, List[ModelType]]:
        if self._results is not None:
            return self._results
        raw_docs = yield from self._cursor.to_list(length=None).__await__()
        instances = []
        for raw_doc in raw_docs:
            instances.append(self._parse_document(raw_doc))
            yield
        self._results = instances
        return instances

    async def __aiter__(self) -> AsyncGenerator[ModelType, None]:
        if self._results is not None:
            for res in self._results:
                yield res
            return
        results = []
        async for raw_doc in self._cursor:
            instance = self._parse_document(raw_doc)
            results.append(instance)
            yield instance
        self._results = results


class SyncCursor(BaseCursor[ModelType], Iterable[ModelType]):
    """This object has to be built from the [odmantic.engine.SyncEngine.find][] method.

    A SyncCursor object supports iterating over the query results using **`for`**.

    To get a list of all the results you can wrap it with `list`, as in `list(cursor)`.
    """

    _cursor: "CommandCursor"

    def __init__(self, model: Type[ModelType], cursor: "CommandCursor"):
        super().__init__(model=model, cursor=cursor)

    def __iter__(self) -> Iterator[ModelType]:
        if self._results is not None:
            for res in self._results:
                yield res
            return
        results = []
        for raw_doc in self._cursor:
            instance = self._parse_document(raw_doc)
            results.append(instance)
            yield instance
        self._results = results


_FORBIDDEN_DATABASE_CHARACTERS = set(("/", "\\", ".", '"', "$"))


class BaseEngine:
    """The BaseEngine is the base class for the async and sync engines. It holds the
    common functionality, like generating the MongoDB queries, that is then used by the
    two engines.
    """

    def __init__(
        self,
        client: Union["AsyncIOMotorClient", "MongoClient"],
        database: str = "test",
    ):
        # https://docs.mongodb.com/manual/reference/limits/#naming-restrictions
        forbidden_characters = _FORBIDDEN_DATABASE_CHARACTERS.intersection(
            set(database)
        )
        if len(forbidden_characters) > 0:
            raise ValueError(
                f"database name cannot contain: {' '.join(forbidden_characters)}"
            )
        self.client = client
        self.database_name = database
        self.database = client[self.database_name]

    @staticmethod
    def _build_query(*queries: Union[QueryExpression, Dict, bool]) -> QueryExpression:
        if len(queries) == 0:
            return QueryExpression()
        for query in queries:
            if isinstance(query, bool):
                raise TypeError("cannot build query using booleans")
        queries = cast(Tuple[Union[QueryExpression, Dict], ...], queries)
        if len(queries) == 1:
            return QueryExpression(queries[0])
        return and_(*queries)

    @staticmethod
    def _cascade_find_pipeline(
        model: Type[ModelType], doc_namespace: str = ""
    ) -> List[Dict]:
        """Recursively build the find pipeline for model."""
        pipeline: List[Dict] = []
        for ref_field_name in model.__references__:
            odm_reference = cast(ODMReference, model.__odm_fields__[ref_field_name])
            pipeline.extend(
                [
                    {
                        "$lookup": {
                            "from": odm_reference.model.__collection__,
                            "let": {"foreign_id": f"${odm_reference.key_name}"},
                            "pipeline": [
                                {
                                    "$match": {
                                        "$expr": {"$eq": ["$_id", "$$foreign_id"]}
                                    }
                                },
                                *BaseEngine._cascade_find_pipeline(
                                    odm_reference.model,
                                    doc_namespace=f"{doc_namespace}{ref_field_name}.",
                                ),
                            ],
                            "as": odm_reference.key_name
                            # FIXME if ref field name is an existing key_name ?
                        }
                    },
                    {  # Preserves document with unbound references
                        "$unwind": {
                            "path": f"${odm_reference.key_name}",
                            "preserveNullAndEmptyArrays": True,
                        }
                    },
                ]
            )
        return pipeline

    @staticmethod
    def _build_sort_expression(
        sort_field: Union[FieldProxy, SortExpression]
    ) -> SortExpression:
        return (
            SortExpression({+sort_field: 1})
            if not isinstance(sort_field, SortExpression)
            else sort_field
        )

    @classmethod
    def _validate_sort_argument(cls, sort: Any) -> Optional[SortExpression]:
        if sort is None:
            return None

        if isinstance(sort, tuple):
            for sorted_field in sort:
                if not isinstance(sorted_field, (FieldProxy, SortExpression)):
                    raise TypeError(
                        "sort elements have to be Model fields or asc, desc descriptors"
                    )
            sort_expression: Dict = {}
            for sort_field in sort:
                sort_expression.update(cls._build_sort_expression(sort_field))

            return SortExpression(sort_expression)

        if not isinstance(sort, (FieldProxy, SortExpression)):
            raise TypeError(
                "sort has to be a Model field or "
                "asc, desc descriptors or a tuple of these"
            )

        return cls._build_sort_expression(sort)

    def _prepare_find_pipeline(
        self,
        model: Type[ModelType],
        *queries: Union[
            QueryExpression, Dict, bool
        ],  # bool: allow using binary operators with mypy
        sort: Optional[Any] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if not lenient_issubclass(model, Model):
            raise TypeError("Can only call find with a Model class")
        sort_expression = self._validate_sort_argument(sort)
        if limit is not None and limit <= 0:
            raise ValueError("limit has to be a strict positive value or None")
        if skip < 0:
            raise ValueError("skip has to be a positive integer")
        query = BaseEngine._build_query(*queries)
        pipeline: List[Dict[str, Any]] = [{"$match": query}]
        if sort_expression is not None:
            pipeline.append({"$sort": sort_expression})
        if skip > 0:
            pipeline.append({"$skip": skip})
        if limit is not None and limit > 0:
            pipeline.append({"$limit": limit})
        pipeline.extend(BaseEngine._cascade_find_pipeline(model))
        return pipeline


class AIOEngine(BaseEngine):
    """The AIOEngine object is responsible for handling database operations with MongoDB
    in an asynchronous way using motor.
    """

    client: "AsyncIOMotorClient"
    database: "AsyncIOMotorDatabase"

    def __init__(
        self,
        client: Union["AsyncIOMotorClient", None] = None,
        database: str = "test",
    ):
        """Engine constructor.

        Args:
            client: instance of an AsyncIO motor client. If None, a default one
                    will be created
            database: name of the database to use

        <!---
        #noqa: DAR401 RuntimeError
        -->
        """
        if not motor:
            raise RuntimeError(
                "motor is required to use AIOEngine, install it with:\n\n"
                + 'pip install "odmantic[motor]"'
            )
        if client is None:
            client = AsyncIOMotorClient()
        super().__init__(client=client, database=database)

    def get_collection(self, model: Type[ModelType]) -> "AsyncIOMotorCollection":
        """Get the motor collection associated to a Model.

        Args:
            model: model class

        Returns:
            the AsyncIO motor collection object
        """
        return self.database[model.__collection__]

    @staticmethod
    def _get_session(
        session: Union[AIOSessionType, AIOSessionBase]
    ) -> Optional[AsyncIOMotorClientSession]:
        if isinstance(session, (AIOSession, AIOTransaction)):
            return session.get_driver_session()
        assert not isinstance(session, AIOSessionBase)  # Abstract class
        return session

    async def configure_database(
        self,
        models: Sequence[Type[ModelType]],
        *,
        update_existing_indexes: bool = False,
        session: SyncSessionType = None,
    ) -> None:
        """Apply model constraints to the database.

        Args:
            models: list of models to initialize the database with
            update_existing_indexes: conflicting indexes will be dropped before creation
            session: an optional session to use for the operation

        <!---
        #noqa: DAR401 pymongo.errors.OperationFailure
        -->
        """
        driver_session = self._get_session(session)
        for model in models:
            collection = self.get_collection(model)
            for index in model.__indexes__():
                pymongo_index = (
                    index.get_pymongo_index()
                    if isinstance(index, ODMBaseIndex)
                    else index
                )
                try:
                    await collection.create_indexes(
                        [pymongo_index], session=driver_session
                    )
                except pymongo.errors.OperationFailure as exc:
                    if update_existing_indexes and getattr(exc, "code", None) in (
                        85,  # aka IndexOptionsConflict
                        86,  # aka IndexKeySpecsConflict for MongoDB > 5
                    ):
                        await collection.drop_index(
                            pymongo_index.document["name"], session=driver_session
                        )
                        await collection.create_indexes(
                            [pymongo_index], session=driver_session
                        )
                    else:
                        raise

    def session(self) -> AIOSession:
        """Get a new session for the engine to allow ordering sequential operations.

        Returns:
            a new session object

        Example usage:

        ```python
        engine = AIOEngine(...)
        async with engine.session() as session:
            john = await session.find(User, User.name == "John")
            john.name = "Doe"
            await session.save(john)
        ```
        """
        return AIOSession(self)

    def transaction(self) -> AIOTransaction:
        """Get a new transaction for the engine to aggregate sequential operations.

        Returns:
            a new transaction object

        Example usage:
        ```python
        engine = AIOEngine(...)
        async with engine.transaction() as transaction:
            john = transaction.find(User, User.name == "John")
            john.name = "Doe"
            await transaction.save(john)
            await transaction.commit()
        ```

        Warning:
            MongoDB transaction are only supported on replicated clusters: either
            directly a replicaSet or a sharded cluster with replication enabled.
        """
        return AIOTransaction(self)

    def find(
        self,
        model: Type[ModelType],
        *queries: Union[
            QueryExpression, Dict, bool
        ],  # bool: allow using binary operators with mypy
        sort: Optional[Any] = None,
        skip: int = 0,
        limit: Optional[int] = None,
        session: AIOSessionType = None,
    ) -> AIOCursor[ModelType]:
        """Search for Model instances matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            sort: sort expression
            skip: number of document to skip
            limit: maximum number of instance fetched
            session: an optional session to use for the operation

        Raises:
            DocumentParsingError: unable to parse one of the resulting documents

        Returns:
            [odmantic.engine.AIOCursor][] of the query

        <!---
        #noqa: DAR401 ValueError
        #noqa: DAR401 TypeError
        #noqa: DAR402 DocumentParsingError
        -->
        """
        pipeline = self._prepare_find_pipeline(
            model,
            *queries,
            sort=sort,
            skip=skip,
            limit=limit,
        )
        collection = self.get_collection(model)
        motor_cursor = collection.aggregate(
            pipeline, session=self._get_session(session)
        )
        return AIOCursor(model, motor_cursor)

    async def find_one(
        self,
        model: Type[ModelType],
        *queries: Union[
            QueryExpression, Dict, bool
        ],  # bool: allow using binary operators w/o plugin
        sort: Optional[Any] = None,
        session: AIOSessionType = None,
    ) -> Optional[ModelType]:
        """Search for a Model instance matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            sort: sort expression
            session: an optional session to use for the operation

        Raises:
            DocumentParsingError: unable to parse the resulting document

        Returns:
            the fetched instance if found otherwise None

        <!---
        #noqa: DAR401 TypeError
        #noqa: DAR402 DocumentParsingError
        -->
        """
        if not lenient_issubclass(model, Model):
            raise TypeError("Can only call find_one with a Model class")
        results = await self.find(model, *queries, sort=sort, limit=1, session=session)
        if len(results) == 0:
            return None
        return results[0]

    async def _save(
        self, instance: ModelType, session: "AsyncIOMotorClientSession"
    ) -> ModelType:
        """Perform an atomic save operation in the specified session"""
        for ref_field_name in instance.__references__:
            sub_instance = cast(Model, getattr(instance, ref_field_name))
            await self._save(sub_instance, session)

        fields_to_update = instance.__fields_modified__ | instance.__mutable_fields__
        if len(fields_to_update) > 0:
            doc = instance.doc(include=fields_to_update)
            collection = self.get_collection(type(instance))
            try:
                await collection.update_one(
                    instance.doc(include={instance.__primary_field__}),
                    {"$set": doc},
                    upsert=True,
                    session=session,
                )
            except pymongo.errors.DuplicateKeyError as e:
                raise DuplicateKeyError(instance, e)
            object.__setattr__(instance, "__fields_modified__", set())
        return instance

    async def save(
        self,
        instance: ModelType,
        *,
        session: AIOSessionType = None,
    ) -> ModelType:
        """Persist an instance to the database

        This method behaves as an 'upsert' operation. If a document already exists
        with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be saved as well.

        Args:
            instance: instance to persist
            session: An optional session to use for the operation. If not provided, an
                     internal session will be used to persist the instance and
                     sub-instances.

        Returns:
            the saved instance

        Raises:
            DuplicateKeyError: the instance is duplicated according to a unique index.

        NOTE:
            The save operation actually modify the instance argument in place. However,
            the instance is still returned for convenience.

        <!---
        #noqa: DAR401 TypeError
        #noqa: DAR402 DuplicateKeyError
        -->
        """
        if not isinstance(instance, Model):
            raise TypeError("Can only call find_one with a Model class")
        if session:
            await self._save(instance, self._get_session(session))
        else:
            async with await self.client.start_session() as local_session:
                await self._save(instance, local_session)
        return instance

    async def save_all(
        self,
        instances: Sequence[ModelType],
        *,
        session: AIOSessionType = None,
    ) -> List[ModelType]:
        """Persist instances to the database

        This method behaves as multiple 'upsert' operations. If one of the document
        already exists with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be recursively saved as
        well.

        Args:
            instances: instances to persist
            session: An optional session to use for the operation. If not provided, an
                     internal session will be used to persist the instances.

        Returns:
            the saved instances

        Raises:
            DuplicateKeyError: an instance is duplicated according to a unique index.

        NOTE:
            The save_all operation actually modify the arguments in place. However, the
            instances are still returned for convenience.

        <!---
        #noqa: DAR402 DuplicateKeyError
        -->
        """
        if session:
            added_instances = [
                await self._save(instance, self._get_session(session))
                for instance in instances
            ]
        else:
            async with await self.client.start_session() as local_session:
                added_instances = [
                    await self._save(instance, local_session) for instance in instances
                ]
        return added_instances

    async def delete(
        self,
        instance: ModelType,
        *,
        session: AIOSessionType = None,
    ) -> None:
        """Delete an instance from the database

        Args:
            instance: the instance to delete
            session: an optional session to use for the operation


        Raises:
            DocumentNotFoundError: the instance has not been persisted to the database
        """
        # TODO handle cascade deletion
        collection = self.database[instance.__collection__]
        pk_name = instance.__primary_field__
        result = await collection.delete_many(
            {"_id": getattr(instance, pk_name)}, session=self._get_session(session)
        )
        count = int(result.deleted_count)
        if count == 0:
            raise DocumentNotFoundError(instance)

    async def remove(
        self,
        model: Type[ModelType],
        *queries: Union[QueryExpression, Dict, bool],
        just_one: bool = False,
        session: AIOSessionType = None,
    ) -> int:
        """Delete Model instances matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            just_one: limit the deletion to just one document
            session: an optional session to use for the operation

        Returns:
            the number of instances deleted from the database.

        """
        query = AIOEngine._build_query(*queries)
        collection = self.get_collection(model)

        if just_one:
            result = await collection.delete_one(
                query, session=self._get_session(session)
            )
        else:
            result = await collection.delete_many(
                query, session=self._get_session(session)
            )

        return cast(int, result.deleted_count)

    async def count(
        self,
        model: Type[ModelType],
        *queries: Union[QueryExpression, Dict, bool],
        session: AIOSessionType = None,
    ) -> int:
        """Get the count of documents matching a query

        Args:
            model: model to perform the operation on
            *queries: query filters to apply
            session: an optional session to use for the operation

        Returns:
            number of document matching the query

        <!---
        #noqa: DAR401 TypeError
        -->
        """
        if not lenient_issubclass(model, Model):
            raise TypeError("Can only call count with a Model class")
        query = BaseEngine._build_query(*queries)
        collection = self.database[model.__collection__]
        count = await collection.count_documents(
            query, session=self._get_session(session)
        )
        return int(count)


class SyncEngine(BaseEngine):
    """The SyncEngine object is responsible for handling database operations with
    MongoDB in an synchronous way using pymongo.
    """

    client: "MongoClient"
    database: "Database"

    def __init__(
        self,
        client: "Union[MongoClient, None]" = None,
        database: str = "test",
    ):
        """Engine constructor.

        Args:
            client: instance of a PyMongo client. If None, a default one
                    will be created
            database: name of the database to use
        """
        if client is None:
            client = MongoClient()
        super().__init__(client=client, database=database)

    def get_collection(self, model: Type[ModelType]) -> "Collection":
        """Get the pymongo collection associated to a Model.

        Args:
            model: model class

        Returns:
            the pymongo collection object
        """
        collection = self.database[model.__collection__]
        return collection

    @staticmethod
    def _get_session(
        session: Union[SyncSessionType, SyncSessionBase]
    ) -> Optional[ClientSession]:
        if isinstance(session, (SyncSession, SyncTransaction)):
            return session.get_driver_session()
        assert not isinstance(session, SyncSessionBase)  # Abstract class
        return session

    def configure_database(
        self,
        models: Sequence[Type[ModelType]],
        *,
        update_existing_indexes: bool = False,
        session: SyncSessionType = None,
    ) -> None:
        """Apply model constraints to the database.

        Args:
            models: list of models to initialize the database with
            update_existing_indexes: conflicting indexes will be dropped before creation
            session: an optional session to use for the operation

        <!---
        #noqa: DAR401 pymongo.errors.OperationFailure
        -->
        """
        driver_session = self._get_session(session)
        for model in models:
            collection = self.get_collection(model)
            for index in model.__indexes__():
                pymongo_index = (
                    index.get_pymongo_index()
                    if isinstance(index, ODMBaseIndex)
                    else index
                )
                try:
                    collection.create_indexes([pymongo_index], session=driver_session)
                except pymongo.errors.OperationFailure as exc:
                    if update_existing_indexes and getattr(exc, "code", None) in (
                        85,  # aka IndexOptionsConflict
                        86,  # aka IndexKeySpecsConflict for MongoDB > 5
                    ):
                        collection.drop_index(
                            pymongo_index.document["name"], session=driver_session
                        )
                        collection.create_indexes(
                            [pymongo_index], session=driver_session
                        )
                    else:
                        raise

    def session(self) -> SyncSession:
        """Get a new session for the engine to allow ordering sequential operations.

        Returns:
            a new session object

        Example usage:

        ```python
        engine = SyncEngine(...)
        with engine.session() as session:
            john = session.find(User, User.name == "John")
            john.name = "Doe"
            session.save(john)
        ```
        """
        return SyncSession(self)

    def transaction(self) -> SyncTransaction:
        """Get a new transaction for the engine to aggregate sequential operations.

        Returns:
            a new transaction object

        Example usage:
        ```python
        engine = SyncEngine(...)
        with engine.transaction() as transaction:
            john = transaction.find(User, User.name == "John")
            john.name = "Doe"
            transaction.save(john)
            transaction.commit()
        ```

        Warning:
            MongoDB transaction are only supported on replicated clusters: either
            directly a replicaSet or a sharded cluster with replication enabled.
        """
        return SyncTransaction(self)

    def find(
        self,
        model: Type[ModelType],
        *queries: Union[
            QueryExpression, Dict, bool
        ],  # bool: allow using binary operators with mypy
        sort: Optional[Any] = None,
        skip: int = 0,
        limit: Optional[int] = None,
        session: SyncSessionType = None,
    ) -> SyncCursor[ModelType]:
        """Search for Model instances matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            sort: sort expression
            skip: number of document to skip
            limit: maximum number of instance fetched
            session: an optional session to use for the operation

        Raises:
            DocumentParsingError: unable to parse one of the resulting documents

        Returns:
            [odmantic.engine.SyncCursor][] of the query

        <!---
        #noqa: DAR401 ValueError
        #noqa: DAR401 TypeError
        #noqa: DAR402 DocumentParsingError
        -->
        """
        pipeline = self._prepare_find_pipeline(
            model,
            *queries,
            sort=sort,
            skip=skip,
            limit=limit,
        )
        collection = self.get_collection(model)
        cursor = collection.aggregate(pipeline, session=self._get_session(session))
        return SyncCursor(model, cursor)

    def find_one(
        self,
        model: Type[ModelType],
        *queries: Union[
            QueryExpression, Dict, bool
        ],  # bool: allow using binary operators w/o plugin
        sort: Optional[Any] = None,
        session: SyncSessionType = None,
    ) -> Optional[ModelType]:
        """Search for a Model instance matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            sort: sort expression
            session: an optional session to use for the operation

        Raises:
            DocumentParsingError: unable to parse the resulting document

        Returns:
            the fetched instance if found otherwise None

        <!---
        #noqa: DAR401 TypeError
        #noqa: DAR402 DocumentParsingError
        -->
        """
        if not lenient_issubclass(model, Model):
            raise TypeError("Can only call find_one with a Model class")
        results = list(self.find(model, *queries, sort=sort, limit=1, session=session))
        if len(results) == 0:
            return None
        return results[0]

    def _save(self, instance: ModelType, session: "ClientSession") -> ModelType:
        """Perform an atomic save operation in the specified session"""
        for ref_field_name in instance.__references__:
            sub_instance = cast(Model, getattr(instance, ref_field_name))
            self._save(sub_instance, session)

        fields_to_update = instance.__fields_modified__ | instance.__mutable_fields__
        if len(fields_to_update) > 0:
            doc = instance.doc(include=fields_to_update)
            collection = self.get_collection(type(instance))
            try:
                collection.update_one(
                    instance.doc(include={instance.__primary_field__}),
                    {"$set": doc},
                    upsert=True,
                    session=session,
                )
            except pymongo.errors.DuplicateKeyError as e:
                raise DuplicateKeyError(instance, e)
            object.__setattr__(instance, "__fields_modified__", set())
        return instance

    def save(
        self,
        instance: ModelType,
        *,
        session: SyncSessionType = None,
    ) -> ModelType:
        """Persist an instance to the database

        This method behaves as an 'upsert' operation. If a document already exists
        with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be saved as well.

        Args:
            instance: instance to persist
            session: An optional session to use for the operation. If not provided, an
                     internal session will be used to persist the instance and
                     sub-instances.

        Returns:
            the saved instance

        Raises:
            DuplicateKeyError: the instance is duplicated according to a unique index.

        NOTE:
            The save operation actually modify the instance argument in place. However,
            the instance is still returned for convenience.

        <!---
        #noqa: DAR401 TypeError
        #noqa: DAR402 DuplicateKeyError
        -->
        """
        if not isinstance(instance, Model):
            raise TypeError("Can only call find_one with a Model class")

        if session:
            self._save(instance, self._get_session(session))  # type: ignore
        else:
            with self.client.start_session() as local_session:
                self._save(instance, local_session)
        return instance

    def save_all(
        self,
        instances: Sequence[ModelType],
        *,
        session: SyncSessionType = None,
    ) -> List[ModelType]:
        """Persist instances to the database

        This method behaves as multiple 'upsert' operations. If one of the document
        already exists with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be recursively saved as
        well.

        Args:
            instances: instances to persist
            session: An optional session to use for the operation. If not provided an
                     internal session will be used to persist the instances.

        Returns:
            the saved instances

        Raises:
            DuplicateKeyError: an instance is duplicated according to a unique index.

        NOTE:
            The save_all operation actually modify the arguments in place. However, the
            instances are still returned for convenience.
        <!---
        #noqa: DAR402 DuplicateKeyError
        -->
        """
        if session:
            added_instances = [
                self._save(instance, self._get_session(session))  # type: ignore
                for instance in instances
            ]
        else:
            with self.client.start_session() as local_session:
                added_instances = [
                    self._save(instance, local_session) for instance in instances
                ]
        return added_instances

    def delete(
        self,
        instance: ModelType,
        session: SyncSessionType = None,
    ) -> None:
        """Delete an instance from the database

        Args:
            instance: the instance to delete
            session: an optional session to use for the operation

        Raises:
            DocumentNotFoundError: the instance has not been persisted to the database

        """
        # TODO handle cascade deletion
        collection = self.database[instance.__collection__]
        pk_name = instance.__primary_field__
        result = collection.delete_many(
            {"_id": getattr(instance, pk_name)}, session=self._get_session(session)
        )
        count = result.deleted_count
        if count == 0:
            raise DocumentNotFoundError(instance)

    def remove(
        self,
        model: Type[ModelType],
        *queries: Union[QueryExpression, Dict, bool],
        just_one: bool = False,
        session: SyncSessionType = None,
    ) -> int:
        """Delete Model instances matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            just_one: limit the deletion to just one document
            session: an optional session to use for the operation

        Returns:
            the number of instances deleted from the database.
        """
        query = SyncEngine._build_query(*queries)
        collection = self.get_collection(model)

        if just_one:
            result = collection.delete_one(query, session=self._get_session(session))
        else:
            result = collection.delete_many(query, session=self._get_session(session))

        return result.deleted_count

    def count(
        self,
        model: Type[ModelType],
        *queries: Union[QueryExpression, Dict, bool],
        session: SyncSessionType = None,
    ) -> int:
        """Get the count of documents matching a query

        Args:
            model: model to perform the operation on
            *queries: query filters to apply
            session: an optional session to use for the operation

        Returns:
            number of document matching the query

        <!---
        #noqa: DAR401 TypeError
        -->
        """
        if not lenient_issubclass(model, Model):
            raise TypeError("Can only call count with a Model class")
        query = BaseEngine._build_query(*queries)
        collection = self.database[model.__collection__]
        count = collection.count_documents(query, session=self._get_session(session))
        return int(count)
