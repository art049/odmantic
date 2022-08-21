from motor.motor_asyncio import AsyncIOMotorClient

from odmantic import AIOEngine

client = AsyncIOMotorClient("mongodb://localhost:27017/")
engine = AIOEngine(motor_client=client, database="example_db")
