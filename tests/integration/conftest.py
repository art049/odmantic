import asyncio
import os
from uuid import uuid4

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic.session import AIOSession

print()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def motor_client(event_loop):
    mongo_uri = os.getenv("TEST_MONGO_URI")
    client = AsyncIOMotorClient(mongo_uri, io_loop=event_loop)
    yield client
    client.close()


@pytest.mark.asyncio
@pytest.fixture(scope="function")
async def session(motor_client):
    database_name = f"odmantic-test-{uuid4()}"
    sess = AIOSession(motor_client, database_name)
    yield sess
    if os.getenv("TEST_DEBUG") is None:
        await motor_client.drop_database(database_name)
