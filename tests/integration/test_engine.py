import pytest

from odmantic.engine import AIOEngine
from odmantic.exceptions import DuplicatePrimaryKeyError
from odmantic.model import EmbeddedModel
from odmantic.types import _objectId

from ..zoo.person import PersonModel

pytestmark = pytest.mark.asyncio


async def test_save(engine: AIOEngine):
    instance = await engine.save(
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    )
    assert isinstance(instance.id, _objectId)


async def test_save_find_find_one(engine: AIOEngine):
    initial_instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    await engine.save(initial_instance)
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


async def test_save_multiple_simple_find_find_one(engine: AIOEngine):
    initial_instances = [
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud"),
        PersonModel(first_name="Jean-Pierre", last_name="Castaldi"),
        PersonModel(first_name="Michel", last_name="Drucker"),
    ]
    await engine.save_all(initial_instances)

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


async def test_find_sync_iteration(engine: AIOEngine):
    instances = [
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud"),
        PersonModel(first_name="Jean-Pierre", last_name="Castaldi"),
        PersonModel(first_name="Michel", last_name="Drucker"),
    ]
    await engine.save_all(instances)

    fetched = set()
    for inst in await engine.find(PersonModel):
        fetched.add(inst.id)

    assert set(i.id for i in instances) == fetched


@pytest.mark.skip("Not implemented yet")
async def test_find_async_iteration(engine: AIOEngine):
    instances = [
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud"),
        PersonModel(first_name="Jean-Pierre", last_name="Castaldi"),
        PersonModel(first_name="Michel", last_name="Drucker"),
    ]
    await engine.save_all(instances)

    fetched = set()
    # TODO Restore the type checking
    async for inst in engine.find(PersonModel):  # type:ignore
        fetched.add(inst.id)

    assert set(i.id for i in instances) == fetched


async def test_save_multiple_time_same_document(engine: AIOEngine):
    fixed_id = _objectId()

    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud", id=fixed_id)
    await engine.save(instance)

    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud", id=fixed_id)
    await engine.save(instance)

    assert await engine.count(PersonModel, PersonModel.id == fixed_id) == 1


@pytest.mark.skip("Not supported yet")
async def test_insert_multiple_time_same_document(engine: AIOEngine):
    fixed_id = _objectId()
    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud", id=fixed_id)
    await engine.insert(instance)  # type: ignore
    with pytest.raises(DuplicatePrimaryKeyError) as exc:
        await engine.insert(instance)  # type: ignore
    assert exc.value.model is PersonModel
    assert exc.value.duplicated_instance == instance
    assert exc.value.duplicated_field == "id"
    assert exc.value.duplicated_value == fixed_id


async def test_count(engine: AIOEngine):
    initial_instances = [
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud"),
        PersonModel(first_name="Jean-Pierre", last_name="Castaldi"),
        PersonModel(first_name="Michel", last_name="Drucker"),
    ]
    await engine.save_all(initial_instances)

    count = await engine.count(PersonModel)
    assert count == 3

    count = await engine.count(PersonModel, PersonModel.first_name == "Michel")
    assert count == 1

    count = await engine.count(PersonModel, PersonModel.first_name == "Gérard")
    assert count == 0


async def test_find_on_embedded(engine: AIOEngine):
    class BadModel(EmbeddedModel):
        field: int

    with pytest.raises(TypeError):
        await engine.find(BadModel)


@pytest.mark.skip("Not implemented")
async def test_save_on_embedded(engine: AIOEngine):
    class BadModel(EmbeddedModel):
        field: int

    instance = BadModel(field=12)
    with pytest.raises(TypeError):
        await engine.save(instance)  # type: ignore


async def test_save_update(engine: AIOEngine):
    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    await engine.save(instance)
    assert await engine.count(PersonModel, PersonModel.last_name == "Pernaud") == 1
    instance.last_name = "Dupuis"
    await engine.save(instance)
    assert await engine.count(PersonModel, PersonModel.last_name == "Pernaud") == 0
    assert await engine.count(PersonModel, PersonModel.last_name == "Dupuis") == 1
