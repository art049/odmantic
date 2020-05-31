import asyncio
from typing import Dict, List, Sequence, Type, TypeVar, Union

from motor.motor_asyncio import AsyncIOMotorClient

from .model import Model
from .types import objectId

ModelType = TypeVar("ModelType", bound=Model)


class AIOSession:
    def __init__(self, motor_client: AsyncIOMotorClient, db_name: str):
        self.client = motor_client
        self.db_name = db_name
        self.database = motor_client[self.db_name]

    def _get_colletion(self, model: Type[ModelType]):
        return self.database[model.__collection__]

    async def find(
        self,
        model: Type[ModelType],
        query: Union[Dict, bool] = {},  # bool: allow using binary operators
        *,
        limit: int = 0,
        skip: int = 0
    ) -> List[ModelType]:
        collection = self._get_colletion(model)
        cursor = collection.find(query)
        cursor = cursor.limit(limit).skip(skip)
        docs = await cursor.to_list(length=None)
        instances = []
        for doc in docs:
            for field_name, mongo_name in model.__odm_name_mapping__:
                doc[field_name] = doc[mongo_name]
                del doc[mongo_name]
            doc["id"] = doc["_id"]
            instance = model.parse_obj(doc)
            instances.append(instance)
        return instances

    async def add(self, instance: ModelType) -> ModelType:
        collection = self._get_colletion(type(instance))

        doc = instance.dict()
        for field_name, mongo_name in instance.__odm_name_mapping__:
            doc[mongo_name] = doc[field_name]
            del doc[field_name]
        if doc["id"] is not None:
            doc["_id"] = doc["id"]
        del doc["id"]
        result = await collection.insert_one(doc, bypass_document_validation=True)
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
