from pymongo import MongoClient

from odmantic import SyncEngine

client = MongoClient("mongodb://localhost:27017/")
engine = SyncEngine(client=client, database="example_db")
