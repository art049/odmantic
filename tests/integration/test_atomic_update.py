import pytest

from odmantic.engine import AIOEngine, SyncEngine

from ..zoo.person import PersonModel

pytestmark = pytest.mark.asyncio


async def test_atomic_update_set(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        await session.save(PersonModel(first_name="John", last_name="Doe"))
        async with session.update(
            PersonModel, PersonModel.first_name == "John"
        ) as person:
            person.last_name = "Doe Doe"
        assert await session.count(PersonModel, PersonModel.last_name == "Doe Doe") == 1


def test_sync_atomic_update_set(sync_engine: SyncEngine):
    with sync_engine.session() as session:
        session.save(PersonModel(first_name="John", last_name="Doe"))
        with session.update(PersonModel, PersonModel.first_name == "John") as person:
            person.last_name = "Doe Doe"
        assert session.count(PersonModel, PersonModel.last_name == "Doe Doe") == 1
