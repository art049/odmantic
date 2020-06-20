import asyncio
from typing import Dict, List, Optional, Sequence, Type, TypeVar, Union

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError as PyMongoDuplicateKeyError

from odmantic.exceptions import DuplicatePrimaryKeyError

from .model import Model
from .types import objectId

ModelType = TypeVar("ModelType", bound=Model)


class AIOEngine:
    def __init__(self, motor_client: AsyncIOMotorClient, db_name: str):
        self.client = motor_client
        self.db_name = db_name
        self.database = motor_client[self.db_name]

    def _get_collection(self, model: Type[ModelType]):
        return self.database[model.__collection__]

    async def find(
        self,
        model: Type[ModelType],
        query: Union[Dict, bool] = {},  # bool: allow using binary operators
        *,
        limit: int = 0,
        skip: int = 0
    ) -> List[ModelType]:
        collection = self._get_collection(model)
        cursor = collection.find(query)
        cursor = cursor.limit(limit).skip(skip)
        docs = await cursor.to_list(length=None)
        instances = []
        for doc in docs:
            for field_name, mongo_name in model.__odm_name_mapping__.items():
                doc[field_name] = doc[mongo_name]
                del doc[mongo_name]
            doc["id"] = doc["_id"]
            instance = model.parse_obj(doc)
            instances.append(instance)
        return instances

    async def find_one(
        self,
        model: Type[ModelType],
        query: Union[Dict, bool] = {},  # bool: allow using binary operators
    ) -> Optional[ModelType]:
        results = await self.find(
            model, query, limit=1
        )  # TODO: check if mongo find_one method is faster
        if len(results) == 0:
            return None
        return results[0]

    async def add(self, instance: ModelType) -> ModelType:
        collection = self._get_collection(type(instance))

        doc = instance.dict()
        for field_name, mongo_name in instance.__odm_name_mapping__.items():
            doc[mongo_name] = doc[field_name]
            del doc[field_name]
        instance_has_existing_id = doc["id"] is not None
        if instance_has_existing_id:
            doc["_id"] = doc["id"]
        del doc["id"]

        try:
            result = await collection.insert_one(doc, bypass_document_validation=True)
        except PyMongoDuplicateKeyError as e:
            if "_id" in e.details["keyPattern"]:
                raise DuplicatePrimaryKeyError(instance)

        if not instance_has_existing_id:
            _id = objectId(str(result.inserted_id))
            instance.__setattr__("id", _id)

        return instance

    async def add_all(self, instances: Sequence[ModelType]) -> List[ModelType]:
        added_instances = await asyncio.gather(
            *[self.add(instance) for instance in instances]
        )
        return added_instances

    async def delete(self, instance: ModelType) -> int:
        collection = self.database[instance.__collection__]
        pk_name = instance.__primary_key__
        if pk_name in instance.__odm_name_mapping__:
            pk_name = instance.__odm_name_mapping__[pk_name]
        result = await collection.delete_many({pk_name: getattr(instance, pk_name)})
        return int(result.deleted_count)
