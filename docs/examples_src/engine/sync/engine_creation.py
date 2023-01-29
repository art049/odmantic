from datetime import timezone

from bson import CodecOptions
from pymongo import MongoClient

from odmantic import SyncEngine

client = MongoClient("mongodb://localhost:27017/")
engine = SyncEngine(
    client=client, 
    database="example_db", 
    codec_options=CodecOptions(tz_aware=True, tzinfo=timezone.utc),
) 