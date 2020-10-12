from typing import Dict, List, Tuple

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from odmantic.bson_fields import _objectId
from odmantic.engine import AIOEngine
from odmantic.exceptions import DocumentNotFoundError
from odmantic.model import EmbeddedModel, Model

from ..zoo.person import PersonModel

pytestmark = pytest.mark.asyncio


async def test_default_motor_client_creation():
    engine = AIOEngine()
    assert isinstance(engine.client, AsyncIOMotorClient)


@pytest.mark.parametrize("illegal_character", ("/", "\\", ".", '"', "$"))
def test_invalid_database_name(illegal_character: str):
    with pytest.raises(ValueError, match="database name cannot contain"):
        AIOEngine(database=f"prefix{illegal_character}suffix")


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


@pytest.fixture(scope="function")
async def person_persisted(engine: AIOEngine):
    initial_instances = [
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud"),
        PersonModel(first_name="Jean-Pierre", last_name="Castaldi"),
        PersonModel(first_name="Michel", last_name="Drucker"),
    ]
    return await engine.save_all(initial_instances)


async def test_save_multiple_simple_find_find_one(
    engine: AIOEngine, person_persisted: List[PersonModel]
):

    found_instances = await engine.find(PersonModel, PersonModel.first_name == "Michel")
    assert len(found_instances) == 1
    assert found_instances[0].first_name == person_persisted[2].first_name
    assert found_instances[0].last_name == person_persisted[2].last_name

    found_instances = await engine.find(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )
    assert len(found_instances) == 2
    assert found_instances[0].id != found_instances[1].id

    single_retrieved = await engine.find_one(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )

    assert single_retrieved is not None
    assert single_retrieved in person_persisted


async def test_find_sync_iteration(
    engine: AIOEngine, person_persisted: List[PersonModel]
):
    fetched = set()
    for inst in await engine.find(PersonModel):
        fetched.add(inst.id)

    assert set(i.id for i in person_persisted) == fetched


@pytest.mark.usefixtures("person_persisted")
async def test_find_sync_iteration_cached(engine: AIOEngine, mock_collection):
    cursor = engine.find(PersonModel)
    initial = await cursor
    collection = mock_collection()
    cached = await cursor
    collection.aggregate.assert_not_awaited()
    assert cached == initial


@pytest.mark.usefixtures("person_persisted")
async def test_find_async_iteration_cached(engine: AIOEngine, mock_collection):
    cursor = engine.find(PersonModel)
    initial = []
    async for inst in cursor:
        initial.append(inst)
    collection = mock_collection()
    cached = []
    async for inst in cursor:
        cached.append(inst)
    collection.aggregate.assert_not_awaited()
    assert cached == initial


async def test_find_skip(engine: AIOEngine, person_persisted: List[PersonModel]):
    results = await engine.find(PersonModel, skip=1)
    assert len(results) == 2
    for instance in results:
        assert instance in person_persisted


async def test_find_one_bad_query(engine: AIOEngine):
    with pytest.raises(TypeError):
        await engine.find_one(PersonModel, True, False)


async def test_find_one_on_non_model(engine: AIOEngine):
    class BadModel:
        pass

    with pytest.raises(TypeError):
        await engine.find_one(BadModel)  # type: ignore


async def test_find_invalid_limit(engine: AIOEngine):
    with pytest.raises(ValueError):
        await engine.find(PersonModel, limit=0)
    with pytest.raises(ValueError):
        await engine.find(PersonModel, limit=-12)


async def test_find_invalid_skip(engine: AIOEngine):
    with pytest.raises(ValueError):
        await engine.find(PersonModel, skip=-1)
    with pytest.raises(ValueError):
        await engine.find(PersonModel, limit=-12)


async def test_save_multiple_time_same_document(engine: AIOEngine):
    fixed_id = _objectId()

    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud", id=fixed_id)
    await engine.save(instance)

    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud", id=fixed_id)
    await engine.save(instance)

    assert await engine.count(PersonModel, PersonModel.id == fixed_id) == 1


@pytest.mark.usefixtures("person_persisted")
async def test_count(engine: AIOEngine):
    count = await engine.count(PersonModel)
    assert count == 3

    count = await engine.count(PersonModel, PersonModel.first_name == "Michel")
    assert count == 1

    count = await engine.count(PersonModel, PersonModel.first_name == "Gérard")
    assert count == 0


async def test_count_on_non_model_fails(engine: AIOEngine):
    class BadModel:
        pass

    with pytest.raises(TypeError):
        await engine.count(BadModel)  # type: ignore


async def test_find_on_embedded_raises(engine: AIOEngine):
    class BadModel(EmbeddedModel):
        field: int

    with pytest.raises(TypeError):
        await engine.find(BadModel)  # type: ignore


async def test_save_on_embedded(engine: AIOEngine):
    class BadModel(EmbeddedModel):
        field: int

    instance = BadModel(field=12)
    with pytest.raises(TypeError):
        await engine.save(instance)  # type: ignore


@pytest.mark.usefixtures("person_persisted")
async def test_implicit_and(engine: AIOEngine):
    count = await engine.count(
        PersonModel,
        PersonModel.first_name == "Michel",
        PersonModel.last_name == "Drucker",
    )
    assert count == 1


async def test_save_update(engine: AIOEngine):
    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    await engine.save(instance)
    assert await engine.count(PersonModel, PersonModel.last_name == "Pernaud") == 1
    instance.last_name = "Dupuis"
    await engine.save(instance)
    assert await engine.count(PersonModel, PersonModel.last_name == "Pernaud") == 0
    assert await engine.count(PersonModel, PersonModel.last_name == "Dupuis") == 1


async def test_delete_and_count(engine: AIOEngine, person_persisted: List[PersonModel]):
    await engine.delete(person_persisted[0])
    assert await engine.count(PersonModel) == 2
    await engine.delete(person_persisted[1])
    assert await engine.count(PersonModel) == 1
    await engine.delete(person_persisted[2])
    assert await engine.count(PersonModel) == 0


async def test_delete_not_existing(engine: AIOEngine):
    non_persisted_instance = PersonModel(first_name="Jean", last_name="Paul")
    with pytest.raises(DocumentNotFoundError) as exc:
        await engine.delete(non_persisted_instance)
    assert exc.value.instance == non_persisted_instance


async def test_modified_fields_cleared_on_document_saved(engine: AIOEngine):
    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    assert len(instance.__fields_modified__) > 0
    await engine.save(instance)
    assert len(instance.__fields_modified__) == 0


@pytest.fixture()
async def engine_one_person(engine: AIOEngine):
    await engine.save(PersonModel(first_name="Jean-Pierre", last_name="Pernaud"))


@pytest.mark.usefixtures("engine_one_person")
async def test_modified_fields_on_find(engine: AIOEngine):
    instance = await engine.find_one(PersonModel)
    assert instance is not None
    assert len(instance.__fields_modified__) == 0


@pytest.mark.usefixtures("engine_one_person")
async def test_modified_fields_on_document_change(engine: AIOEngine):
    instance = await engine.find_one(PersonModel)
    assert instance is not None
    instance.first_name = "Jackie"
    assert len(instance.__fields_modified__) == 1
    instance.last_name = "Chan"
    assert len(instance.__fields_modified__) == 2


@pytest.mark.usefixtures("engine_one_person")
async def test_no_set_on_save_fetched_document(engine: AIOEngine, mock_collection):
    instance = await engine.find_one(PersonModel)
    assert instance is not None

    collection = mock_collection()
    await engine.save(instance)
    collection.update_one.assert_not_awaited()


@pytest.mark.usefixtures("engine_one_person")
async def test_only_modified_set_on_save(engine: AIOEngine, mock_collection):
    instance = await engine.find_one(PersonModel)
    assert instance is not None

    instance.first_name = "John"
    collection = mock_collection()
    await engine.save(instance)
    collection.update_one.assert_awaited_once()
    (_, set_arg), _ = collection.update_one.await_args
    assert set_arg == {"$set": {"first_name": "John"}}


async def test_only_mutable_list_set_on_save(engine: AIOEngine, mock_collection):
    class M(Model):
        field: List[str]
        immutable_field: int

    instance = M(field=["hello"], immutable_field=12)
    await engine.save(instance)

    collection = mock_collection()
    await engine.save(instance)
    collection.update_one.assert_awaited_once()
    (_, set_arg), _ = collection.update_one.await_args
    set_dict = set_arg["$set"]
    assert list(set_dict.keys()) == ["field"]


async def test_only_mutable_list_of_embedded_set_on_save(
    engine: AIOEngine, mock_collection
):
    class E(EmbeddedModel):
        a: str

    class M(Model):
        field: List[E]

    instance = M(field=[E(a="hello")])
    await engine.save(instance)

    collection = mock_collection()
    await engine.save(instance)
    collection.update_one.assert_awaited_once()
    (_, set_arg), _ = collection.update_one.await_args
    set_dict = set_arg["$set"]
    assert set_dict == {"field": [{"a": "hello"}]}


async def test_only_mutable_dict_of_embedded_set_on_save(
    engine: AIOEngine, mock_collection
):
    class E(EmbeddedModel):
        a: str

    class M(Model):
        field: Dict[str, E]

    instance = M(field={"hello": E(a="world")})
    await engine.save(instance)

    collection = mock_collection()
    await engine.save(instance)
    collection.update_one.assert_awaited_once()
    (_, set_arg), _ = collection.update_one.await_args
    set_dict = set_arg["$set"]
    assert set_dict == {"field": {"hello": {"a": "world"}}}


async def test_only_tuple_of_embedded_set_on_save(engine: AIOEngine, mock_collection):
    class E(EmbeddedModel):
        a: str

    class M(Model):
        field: Tuple[E]

    instance = M(field=(E(a="world"),))
    await engine.save(instance)

    collection = mock_collection()
    await engine.save(instance)
    collection.update_one.assert_awaited_once()
    (_, set_arg), _ = collection.update_one.await_args
    set_dict = set_arg["$set"]
    assert set_dict == {"field": ({"a": "world"},)}
