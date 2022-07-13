import asyncio
import os
from enum import Enum
from unittest.mock import Mock
from uuid import uuid4

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from odmantic.engine import AIOEngine

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


@pytest.fixture(scope="session")
def event_loop():
    asyncio.get_event_loop().close()
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def motor_client(event_loop):
    mongo_uri = TEST_MONGO_URI
    client = AsyncIOMotorClient(mongo_uri, io_loop=event_loop)
    yield client
    client.close()


@pytest.fixture(scope="function")
def database_name():
    return f"odmantic-test-{uuid4()}"


@pytest.mark.asyncio
@pytest.fixture(scope="function")
async def engine(motor_client, database_name):
    sess = AIOEngine(motor_client, database_name)
    yield sess
    if os.getenv("TEST_DEBUG") is None:
        await motor_client.drop_database(database_name)


@pytest.fixture(scope="function")
def motor_database(database_name, motor_client):
    return motor_client[database_name]


@pytest.fixture(scope="function")
def mock_collection(engine: AIOEngine, monkeypatch):
    def f():
        collection = Mock()
        collection.update_one = AsyncMock()
        collection.aggregate = AsyncMock()
        monkeypatch.setattr(engine, "get_collection", lambda _: collection)
        return collection

    return f
