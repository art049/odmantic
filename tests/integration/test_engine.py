import pytest

from odmantic.engine import AIOEngine
from odmantic.types import objectId

from ..zoo.person import PersonModel

pytestmark = pytest.mark.asyncio


async def test_add(engine: AIOEngine):
    instance = await engine.add(
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    )
    assert isinstance(instance.id, objectId)


async def test_add_find_find_one(engine: AIOEngine):
    initial_instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    await engine.add(initial_instance)
    found_instances = await engine.find(PersonModel)
    assert len(found_instances) == 1
    assert found_instances[0].first_name == initial_instance.first_name
    assert found_instances[0].last_name == initial_instance.last_name

    single_fetched_instance = await engine.find_one(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )
    assert single_fetched_instance is not None
    assert single_fetched_instance.first_name == initial_instance.first_name
    assert single_fetched_instance.last_name == initial_instance.last_name


async def test_find_one_not_existing(engine: AIOEngine):
    fetched = await engine.find_one(PersonModel)
    assert fetched is None


async def test_add_multiple_simple_find_find_one(engine: AIOEngine):
    initial_instances = [
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud"),
        PersonModel(first_name="Jean-Pierre", last_name="Castaldi"),
        PersonModel(first_name="Michel", last_name="Drucker"),
    ]
    await engine.add_all(initial_instances)

    found_instances = await engine.find(PersonModel, PersonModel.first_name == "Michel")
    assert len(found_instances) == 1
    assert found_instances[0].first_name == initial_instances[2].first_name
    assert found_instances[0].last_name == initial_instances[2].last_name

    found_instances = await engine.find(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )
    assert len(found_instances) == 2
    assert found_instances[0].id != found_instances[1].id

    single_retrieved = await engine.find_one(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )

    assert single_retrieved is not None
    assert single_retrieved in initial_instances
