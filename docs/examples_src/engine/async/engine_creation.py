from datetime import timezone

from bson import CodecOptions
from motor.motor_asyncio import AsyncIOMotorClient

from odmantic import AIOEngine

client = AsyncIOMotorClient("mongodb://localhost:27017/")
engine = AIOEngine(
    client=client, 
    database="example_db", 
    codec_options=CodecOptions(tz_aware=True, tzinfo=timezone.utc),
) 