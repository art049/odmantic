import asyncio
import os
from enum import Enum
from unittest.mock import Mock
from uuid import uuid4

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from odmantic.engine import AIOEngine, SyncEngine

try:
    from unittest.mock import AsyncMock
except ImportError:
    from mock import AsyncMock  # type: ignore

TEST_MONGO_URI: str = os.getenv("TEST_MONGO_URI", "mongodb://localhost:27017/")


class MongoMode(str, Enum):
    REPLICA = "replicaSet"
    SHARDED = "sharded"
    STANDALONE = "standalone"
    DEFAULT = "default"


TEST_MONGO_MODE = MongoMode(os.getenv("TEST_MONGO_MODE", "default"))

only_on_replica = pytest.mark.skipif(
    TEST_MONGO_MODE != MongoMode.REPLICA,
    reason="Test transactions only with replicas/shards, as it's only supported there",
)


@pytest_asyncio.fixture(scope="function")
async def motor_client():
    mongo_uri = TEST_MONGO_URI
    client = AsyncIOMotorClient(mongo_uri)
    yield client
    client.close()


@pytest.fixture(scope="session")
def pymongo_client():
    mongo_uri = TEST_MONGO_URI
    client: MongoClient = MongoClient(mongo_uri)
    yield client
    client.close()


@pytest.fixture(scope="function")
def database_name():
    return f"odmantic-test-{uuid4()}"


@pytest_asyncio.fixture(scope="function")
async def aio_engine(motor_client: AsyncIOMotorClient, database_name: str):
    sess = AIOEngine(motor_client, database_name)
    yield sess
    if os.getenv("TEST_DEBUG") is None:
        await motor_client.drop_database(database_name)
    else:
        print(f"Database {database_name} not dropped")


@pytest.fixture(scope="function")
def sync_engine(pymongo_client: MongoClient, database_name: str):
    sess = SyncEngine(pymongo_client, database_name)
    yield sess
    if os.getenv("TEST_DEBUG") is None:
        pymongo_client.drop_database(database_name)


@pytest_asyncio.fixture(scope="function")
async def motor_database(database_name: str, motor_client: AsyncIOMotorClient):
    return motor_client[database_name]


@pytest.fixture(scope="function")
def pymongo_database(database_name: str, pymongo_client: MongoClient):
    return pymongo_client[database_name]


@pytest_asyncio.fixture(scope="function")
async def aio_mock_collection(aio_engine: AIOEngine, monkeypatch):
    def f():
        collection = Mock()
        collection.update_one = AsyncMock()
        collection.aggregate = AsyncMock()
        monkeypatch.setattr(aio_engine, "get_collection", lambda _: collection)
        return collection

    return f


@pytest.fixture(scope="function")
def sync_mock_collection(sync_engine: SyncEngine, monkeypatch):
    def f():
        collection = Mock()
        collection.update_one = Mock()
        collection.aggregate = Mock()
        monkeypatch.setattr(sync_engine, "get_collection", lambda _: collection)
        return collection

    return f
