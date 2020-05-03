import asyncio
from typing import Dict, Generic, List, Sequence, Type, TypeVar

from motor.motor_asyncio import AsyncIOMotorClient

from .fields import ObjectId
from .model import Model

ModelType = TypeVar("ModelType", bound=Model)


class Cursor(Generic[ModelType]):
    def all(self) -> List[ModelType]:
        ...


class AIOSession:
    def __init__(self, motor_client: AsyncIOMotorClient, db_name: str):
        self.client = motor_client
        self.db_name = db_name
        self.database = motor_client[self.db_name]

    async def find(
        self, model: Type[ModelType], query: Dict = {}, *, limit: int = 0, skip: int = 0
    ) -> List[ModelType]:
        collection = self.database[model.__collection__]
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
        collection = self.database[instance.__collection__]
        doc = instance.dict()
        for field_name, mongo_name in instance.__odm_name_mapping__:
            doc[mongo_name] = doc[field_name]
            del doc[field_name]
        if doc["id"] is not None:
            doc["_id"] = doc["id"]
        del doc["id"]
        result = await collection.insert_one(doc, bypass_document_validation=True)
        _id = ObjectId(str(result.inserted_id))
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
