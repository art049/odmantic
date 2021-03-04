import asyncio
from asyncio.tasks import gather
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterable,
    Awaitable,
    Dict,
    Generator,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorClientSession,
    AsyncIOMotorCollection,
    AsyncIOMotorCursor,
)
from pydantic.utils import lenient_issubclass

from odmantic.exceptions import DocumentNotFoundError
from odmantic.field import FieldProxy, ODMReference
from odmantic.model import Model
from odmantic.query import QueryExpression, SortExpression, and_

ModelType = TypeVar("ModelType", bound=Model)

SortExpressionType = Optional[Union[FieldProxy, Tuple[FieldProxy]]]


class AIOCursor(
    Generic[ModelType], AsyncIterable[ModelType], Awaitable[List[ModelType]]
):
    """This object has to be built from the [odmantic.engine.AIOEngine.find][] method.

    An AIOCursor object support multiple async operations:

      - **async for**: asynchronously iterate over the query results
      - **await** : when awaited it will return a list of the fetched models
    """

    def __init__(self, model: Type[ModelType], motor_cursor: AsyncIOMotorCursor):
        self._model = model
        self._motor_cursor = motor_cursor
        self._results: Optional[List[ModelType]] = None

    def _parse_document(self, raw_doc: Dict) -> ModelType:
        instance = self._model.parse_doc(raw_doc)
        object.__setattr__(instance, "__fields_modified__", set())
        return instance

    def __await__(self) -> Generator[None, None, List[ModelType]]:
        if self._results is not None:
            return self._results
        raw_docs = yield from self._motor_cursor.to_list(length=None).__await__()
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
        async for raw_doc in self._motor_cursor:
            instance = self._parse_document(raw_doc)
            results.append(instance)
            yield instance
        self._results = results


_FORBIDDEN_DATABASE_CHARACTERS = set(("/", "\\", ".", '"', "$"))


class AIOEngine:
    """The AIOEngine object is responsible for handling database operations with MongoDB
    in an asynchronous way using motor.
    """

    def __init__(self, motor_client: AsyncIOMotorClient = None, database: str = "test"):
        """Engine constructor.

        Args:
            motor_client: instance of an AsyncIO motor client. If None, a default one
                    will be created
            database: name of the database to use

        <!---
        #noqa: DAR401 ValueError
        -->
        """
        # https://docs.mongodb.com/manual/reference/limits/#naming-restrictions
        forbidden_characters = _FORBIDDEN_DATABASE_CHARACTERS.intersection(
            set(database)
        )
        if len(forbidden_characters) > 0:
            raise ValueError(
                f"database name cannot contain: {' '.join(forbidden_characters)}"
            )
        if motor_client is None:
            motor_client = AsyncIOMotorClient()
        self.client = motor_client
        self.database_name = database
        self.database = motor_client[self.database_name]

    def get_collection(self, model: Type[ModelType]) -> AsyncIOMotorCollection:
        """Get the motor collection associated to a Model.

        Args:
            model: model class

        Returns:
            the AsyncIO motor collection object
        """
        return self.database[model.__collection__]

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
                                *AIOEngine._cascade_find_pipeline(
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

    def find(
        self,
        model: Type[ModelType],
        *queries: Union[
            QueryExpression, Dict, bool
        ],  # bool: allow using binary operators with mypy
        sort: Optional[Any] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> AIOCursor[ModelType]:
        """Search for Model instances matching the query filter provided

        Args:
            model: model to perform the operation on
            queries: query filter to apply
            sort: sort expression
            skip: number of document to skip
            limit: maximum number of instance fetched

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
        if not lenient_issubclass(model, Model):
            raise TypeError("Can only call find with a Model class")
        sort_expression = self._validate_sort_argument(sort)
        if limit is not None and limit <= 0:
            raise ValueError("limit has to be a strict positive value or None")
        if skip < 0:
            raise ValueError("skip has to be a positive integer")
        query = AIOEngine._build_query(*queries)
        collection = self.get_collection(model)
        pipeline: List[Dict] = [{"$match": query}]
        if sort_expression is not None:
            pipeline.append({"$sort": sort_expression})
        if skip > 0:
            pipeline.append({"$skip": skip})
        if limit is not None and limit > 0:
            pipeline.append({"$limit": limit})
        pipeline.extend(AIOEngine._cascade_find_pipeline(model))
        motor_cursor = collection.aggregate(pipeline)
        return AIOCursor(model, motor_cursor)

    async def find_one(
        self,
        model: Type[ModelType],
        *queries: Union[
            QueryExpression, Dict, bool
        ],  # bool: allow using binary operators w/o plugin,
        sort: Optional[Any] = None,
    ) -> Optional[ModelType]:
        """Search for a Model instance matching the query filter provided

        Args:
            model: model to perform the operation on
            queries: query filter to apply
            sort: sort expression

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
        results = await self.find(model, *queries, sort=sort, limit=1)
        if len(results) == 0:
            return None
        return results[0]

    async def _save(
        self, instance: ModelType, session: AsyncIOMotorClientSession
    ) -> ModelType:
        """Perform an atomic save operation in the specified session"""
        save_tasks = []
        for ref_field_name in instance.__references__:
            sub_instance = cast(Model, getattr(instance, ref_field_name))
            save_tasks.append(self._save(sub_instance, session))

        await gather(*save_tasks)
        fields_to_update = (
            instance.__fields_modified__ | instance.__mutable_fields__
        ) - set([instance.__primary_field__])
        if len(fields_to_update) > 0:
            doc = instance.doc(include=fields_to_update)
            collection = self.get_collection(type(instance))
            await collection.update_one(
                {"_id": getattr(instance, instance.__primary_field__)},
                {"$set": doc},
                upsert=True,
            )
            object.__setattr__(instance, "__fields_modified__", set())
        return instance

    async def save(self, instance: ModelType) -> ModelType:
        """Persist an instance to the database

        This method behaves as an 'upsert' operation. If a document already exists
        with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be saved as well.

        Args:
            instance: instance to persist

        Returns:
            the saved instance

        NOTE:
            The save operation actually modify the instance argument in place. However,
            the instance is still returned for convenience.

        <!---
        #noqa: DAR401 TypeError
        -->
        """
        if not isinstance(instance, Model):
            raise TypeError("Can only call find_one with a Model class")

        async with await self.client.start_session() as s:
            async with s.start_transaction():
                await self._save(instance, s)
        return instance

    async def save_all(self, instances: Sequence[ModelType]) -> List[ModelType]:
        """Persist instances to the database

        This method behaves as multiple 'upsert' operations. If one of the document
        already exists with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be recursively saved as
        well.

        Args:
            instances: instances to persist

        Returns:
            the saved instances

        NOTE:
            The save_all operation actually modify the arguments in place. However, the
            instances are still returned for convenience.
        """
        async with await self.client.start_session() as s:
            async with s.start_transaction():
                added_instances = await asyncio.gather(
                    *[self._save(instance, s) for instance in instances]
                )
        return added_instances

    async def delete(self, instance: ModelType) -> None:
        """Delete an instance from the database

        Args:
            instance: the instance to delete

        Raises:
            DocumentNotFoundError: the instance has not been persisted to the database

        """
        # TODO handle cascade deletion
        collection = self.database[instance.__collection__]
        pk_name = instance.__primary_field__
        result = await collection.delete_many({"_id": getattr(instance, pk_name)})
        count = int(result.deleted_count)
        if count == 0:
            raise DocumentNotFoundError(instance)

    async def count(
        self, model: Type[ModelType], *queries: Union[QueryExpression, Dict, bool]
    ) -> int:
        """Get the count of documents matching a query

        Args:
            model: model to perform the operation on
            queries: query filters to apply

        Returns:
            number of document matching the query

        <!---
        #noqa: DAR401 TypeError
        -->
        """
        if not lenient_issubclass(model, Model):
            raise TypeError("Can only call count with a Model class")
        query = AIOEngine._build_query(*queries)
        collection = self.database[model.__collection__]
        count = await collection.count_documents(query)
        return int(count)
