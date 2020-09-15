import asyncio
from asyncio.tasks import gather
from typing import (
    AsyncIterable,
    Awaitable,
    Dict,
    Generator,
    Generic,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorClientSession,
    AsyncIOMotorCursor,
)
from pydantic.utils import lenient_issubclass
from pymongo.errors import DuplicateKeyError as PyMongoDuplicateKeyError

from odmantic.exceptions import DocumentNotFoundError, DuplicatePrimaryKeyError
from odmantic.fields import ODMReference
from odmantic.model import Model
from odmantic.query import QueryExpression

ModelType = TypeVar("ModelType", bound=Model)


class AIOCursor(
    Generic[ModelType], AsyncIterable[ModelType], Awaitable[List[ModelType]]
):
    """
    This object has to be built from the [odmantic.engine.AIOEngine.find][] method.

    The AIOCursor support multiple async operations:

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

    async def __aiter__(self):
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


class AIOEngine:
    """
    The AIOEngine object is responsible for handling database operations with MongoDB in
    an asynchronous way using motor.
    """

    def __init__(self, motor_client: AsyncIOMotorClient, db_name: str):
        """
        Args:
            motor_client: instance of an AsyncIO motor client
            db_name: name of the database to use
        """
        self.client = motor_client
        self.db_name = db_name
        self.database = motor_client[self.db_name]

    def _get_collection(self, model: Type[ModelType]):
        return self.database[model.__collection__]

    @staticmethod
    def _cascade_find_pipeline(
        model: Type[ModelType], doc_namespace: str = ""
    ) -> List[Dict]:
        """Recursively build the find pipeline for model"""
        pipeline: List[Dict] = []
        for ref_field_name in model.__references__:
            odm_reference = cast(ODMReference, model.__odm_fields__[ref_field_name])
            pipeline.append(
                {
                    "$lookup": {
                        "from": odm_reference.model.__collection__,
                        "let": {"foreign_id": f"${odm_reference.key_name}"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$_id", "$$foreign_id"]}}},
                            *AIOEngine._cascade_find_pipeline(
                                odm_reference.model,
                                doc_namespace=f"{doc_namespace}{ref_field_name}.",
                            ),
                        ],
                        "as": ref_field_name
                        # FIXME if ref field name is an existing key_name ?
                    }
                }
            )
            pipeline.append({"$unwind": f"${ref_field_name}"})
        return pipeline

    def find(
        self,
        model: Type[ModelType],
        query: Union[
            QueryExpression, Dict, bool
        ] = QueryExpression(),  # bool: allow using binary operators with mypy
        *,
        limit: Optional[int] = None,
        skip: int = 0,
    ) -> AIOCursor[ModelType]:
        """Search for Model instances matching the query filter provided

        Args:
            model: model to perform the operation on
            query: query filter to apply
            limit: maximum number of instance fetched
            skip: number of document to skip


        Returns:
            [odmantic.engine.AIOCursor][] of the query
        """
        if not lenient_issubclass(model, Model):
            raise TypeError("Can only call find with a Model class")
        if limit is not None and limit <= 0:
            raise ValueError("limit has to be a strict positive value or None")
        if skip < 0:
            raise ValueError("skip has to be a positive integer")

        collection = self._get_collection(model)
        pipeline: List[Dict] = [{"$match": query}]
        if limit is not None and limit > 0:
            pipeline.append({"$limit": limit})
        if skip > 0:
            pipeline.append({"$skip": skip})
        pipeline.extend(AIOEngine._cascade_find_pipeline(model))
        motor_cursor = collection.aggregate(pipeline)
        return AIOCursor(model, motor_cursor)

    async def find_one(
        self,
        model: Type[ModelType],
        query: Union[
            QueryExpression, Dict, bool
        ] = QueryExpression(),  # bool: allow using binary operators w/o plugin
    ) -> Optional[ModelType]:
        """Search for a Model instance matching the query filter provided

        Args:
            model: model to perform the operation on
            query: query filter to apply

        Returns:
            the fetched instance if found otherwise None
        """
        if not lenient_issubclass(model, Model):
            raise TypeError("Can only call find_one with a Model class")
        results = await self.find(model, query, limit=1)
        if len(results) == 0:
            return None
        return results[0]

    async def _save(
        self, instance: ModelType, session: AsyncIOMotorClientSession
    ) -> ModelType:
        """
        Perform an atomic save operation in the specified session
        """
        save_tasks = []
        for ref_field_name in instance.__references__:
            sub_instance = cast(Model, getattr(instance, ref_field_name))
            save_tasks.append(self._save(sub_instance, session))

        await gather(*save_tasks)

        if len(instance.__fields_modified__):
            doc = instance.doc(
                include=(instance.__fields_modified__ - set([instance.__primary_key__]))
            )
            collection = self._get_collection(type(instance))
            await collection.update_one(
                {"_id": instance.id},
                {"$set": doc},
                upsert=True,
                bypass_document_validation=True,
            )
        return instance

    async def save(self, instance: ModelType) -> ModelType:
        """
        Persist an instance to the database

        This method behaves as an 'upsert' operation. If a document already exists
        with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be saved as well.

        Args:
            instance (ModelType): [description]

        Returns:
            the saved instance

        NOTE:
            the save operation actually modify the instance argument in place. The
            instance is still returned for convenience.
        """
        try:
            async with await self.client.start_session() as s:
                async with s.start_transaction():
                    await self._save(instance, s)
            object.__setattr__(instance, "__fields_modified__", set())
        except PyMongoDuplicateKeyError as e:
            if "_id" in e.details["keyPattern"]:
                raise DuplicatePrimaryKeyError(instance)
            raise
        return instance

    async def save_all(self, instances: Sequence[ModelType]) -> List[ModelType]:
        """
        Persist instances to the database

        This method behaves as multiple 'upsert' operations. If one of the document
        already exists with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be recursively saved as
        well.

        Args:
            instances (Sequence[ModelType]): [description]

        Returns:
            the saved instances

        NOTE:
            the save_all operation actually modify the arguments in place. The
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
        pk_name = instance.__primary_key__
        result = await collection.delete_many({"_id": getattr(instance, pk_name)})
        count = int(result.deleted_count)
        if count == 0:
            raise DocumentNotFoundError(instance)

    async def count(
        self, model: Type[ModelType], query: Union[QueryExpression, Dict, bool] = {}
    ) -> int:
        """Get the count of document matching a query

        Args:
            model: model to perform the operation on
            query: query filter to apply

        Returns:
            number of document matching the query
        """
        if not lenient_issubclass(model, Model):
            raise TypeError("Can only call count with a Model class")
        collection = self.database[model.__collection__]
        count = await collection.count_documents(query)
        return int(count)
