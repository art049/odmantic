from typing import Dict, List, Optional, Tuple

import pytest
from bson import ObjectId as BsonObjectId
from inline_snapshot import snapshot
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from odmantic.bson import ObjectId
from odmantic.engine import AIOEngine, SyncEngine
from odmantic.exceptions import DocumentNotFoundError, DocumentParsingError
from odmantic.field import Field
from odmantic.model import EmbeddedModel, Model
from odmantic.query import asc, desc
from tests.integration.conftest import only_on_replica
from tests.integration.utils import redact_objectid
from tests.zoo.book_reference import Book, Publisher

from ..zoo.person import PersonModel

pytestmark = pytest.mark.asyncio


def test_default_motor_client_creation():
    engine = AIOEngine()
    assert isinstance(engine.client, AsyncIOMotorClient)


def test_no_motor_raises_for_aioengine_client_creation():
    import odmantic.engine

    motor = odmantic.engine.motor
    odmantic.engine.motor = None
    with pytest.raises(RuntimeError) as e:
        AIOEngine()
    assert 'pip install "odmantic[motor]"' in str(e)
    odmantic.engine.motor = motor


def test_default_pymongo_client_creation():
    engine = SyncEngine()
    assert isinstance(engine.client, MongoClient)


def test_no_motor_passes_with_syncengine_client_creation():
    import odmantic.engine

    motor = odmantic.engine.motor
    odmantic.engine.motor = None
    engine = SyncEngine()
    assert isinstance(engine.client, MongoClient)
    odmantic.engine.motor = motor


@pytest.mark.parametrize("illegal_character", ("/", "\\", ".", '"', "$"))
def test_invalid_database_name(illegal_character: str):
    with pytest.raises(ValueError, match="database name cannot contain"):
        AIOEngine(database=f"prefix{illegal_character}suffix")
    with pytest.raises(ValueError, match="database name cannot contain"):
        SyncEngine(database=f"prefix{illegal_character}suffix")


async def test_save(aio_engine: AIOEngine):
    instance = await aio_engine.save(
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    )
    assert isinstance(instance.id, BsonObjectId)


def test_sync_save(sync_engine: SyncEngine):
    instance = sync_engine.save(
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    )
    assert isinstance(instance.id, BsonObjectId)


async def test_save_find_find_one(aio_engine: AIOEngine):
    initial_instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    await aio_engine.save(initial_instance)
    found_instances = await aio_engine.find(PersonModel)
    assert len(found_instances) == 1
    assert found_instances[0].first_name == initial_instance.first_name
    assert found_instances[0].last_name == initial_instance.last_name

    single_fetched_instance = await aio_engine.find_one(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )
    assert single_fetched_instance is not None
    assert single_fetched_instance.first_name == initial_instance.first_name
    assert single_fetched_instance.last_name == initial_instance.last_name


def test_sync_save_find_find_one(sync_engine: SyncEngine):
    initial_instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    sync_engine.save(initial_instance)
    found_instances = list(sync_engine.find(PersonModel))
    assert len(found_instances) == 1
    assert found_instances[0].first_name == initial_instance.first_name
    assert found_instances[0].last_name == initial_instance.last_name

    single_fetched_instance = sync_engine.find_one(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )
    assert single_fetched_instance is not None
    assert single_fetched_instance.first_name == initial_instance.first_name
    assert single_fetched_instance.last_name == initial_instance.last_name


async def test_find_one_not_existing(aio_engine: AIOEngine):
    fetched = await aio_engine.find_one(PersonModel)
    assert fetched is None


def test_sync_find_one_not_existing(sync_engine: SyncEngine):
    fetched = sync_engine.find_one(PersonModel)
    assert fetched is None


@pytest.fixture(scope="function")
async def person_persisted(aio_engine: AIOEngine):
    initial_instances = [
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud"),
        PersonModel(first_name="Jean-Pierre", last_name="Castaldi"),
        PersonModel(first_name="Michel", last_name="Drucker"),
    ]
    return await aio_engine.save_all(initial_instances)


async def test_save_multiple_simple_find_find_one(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    found_instances = await aio_engine.find(
        PersonModel, PersonModel.first_name == "Michel"
    )
    assert len(found_instances) == 1
    assert found_instances[0].first_name == person_persisted[2].first_name
    assert found_instances[0].last_name == person_persisted[2].last_name

    found_instances = await aio_engine.find(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )
    assert len(found_instances) == 2
    assert found_instances[0].id != found_instances[1].id

    single_retrieved = await aio_engine.find_one(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )

    assert single_retrieved is not None
    assert single_retrieved in person_persisted


def test_sync_save_multiple_simple_find_find_one(
    sync_engine: SyncEngine, person_persisted: List[PersonModel]
):
    found_instances = list(
        sync_engine.find(PersonModel, PersonModel.first_name == "Michel")
    )
    assert len(found_instances) == 1
    assert found_instances[0].first_name == person_persisted[2].first_name
    assert found_instances[0].last_name == person_persisted[2].last_name

    found_instances = list(
        sync_engine.find(PersonModel, PersonModel.first_name == "Jean-Pierre")
    )
    assert len(found_instances) == 2
    assert found_instances[0].id != found_instances[1].id

    single_retrieved = sync_engine.find_one(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )

    assert single_retrieved is not None
    assert single_retrieved in person_persisted


async def test_find_sync_iteration(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    fetched = set()
    for inst in await aio_engine.find(PersonModel):
        fetched.add(inst.id)

    assert set(i.id for i in person_persisted) == fetched


def test_sync_find_sync_iteration(
    sync_engine: SyncEngine, person_persisted: List[PersonModel]
):
    fetched = set()
    for inst in sync_engine.find(PersonModel):
        fetched.add(inst.id)

    assert set(i.id for i in person_persisted) == fetched


@pytest.mark.usefixtures("person_persisted")
async def test_find_sync_iteration_cached(aio_engine: AIOEngine, aio_mock_collection):
    cursor = aio_engine.find(PersonModel)
    initial = await cursor
    collection = aio_mock_collection()
    cached = await cursor
    collection.aggregate.assert_not_awaited()
    assert cached == initial


@pytest.mark.usefixtures("person_persisted")
def test_sync_find_sync_iteration_cached(sync_engine: SyncEngine, sync_mock_collection):
    cursor = sync_engine.find(PersonModel)
    initial = list(cursor)
    collection = sync_mock_collection()
    cached = list(cursor)
    collection.aggregate.assert_not_called()
    assert cached == initial


@pytest.mark.usefixtures("person_persisted")
async def test_find_async_iteration_cached(aio_engine: AIOEngine, aio_mock_collection):
    cursor = aio_engine.find(PersonModel)
    initial = []
    async for inst in cursor:
        initial.append(inst)
    collection = aio_mock_collection()
    cached = []
    async for inst in cursor:
        cached.append(inst)
    collection.aggregate.assert_not_awaited()
    assert cached == initial


@pytest.mark.usefixtures("person_persisted")
def test_sync_find_async_iteration_cached(
    sync_engine: SyncEngine, sync_mock_collection
):
    cursor = sync_engine.find(PersonModel)
    initial = []
    for inst in cursor:
        initial.append(inst)
    collection = sync_mock_collection()
    cached = []
    for inst in cursor:
        cached.append(inst)
    collection.aggregate.assert_not_called()
    assert cached == initial


async def test_find_skip(aio_engine: AIOEngine, person_persisted: List[PersonModel]):
    results = await aio_engine.find(PersonModel, skip=1)
    assert len(results) == 2
    for instance in results:
        assert instance in person_persisted


def test_sync_find_skip(sync_engine: SyncEngine, person_persisted: List[PersonModel]):
    results = list(sync_engine.find(PersonModel, skip=1))
    assert len(results) == 2
    for instance in results:
        assert instance in person_persisted


async def test_find_one_bad_query(aio_engine: AIOEngine):
    with pytest.raises(TypeError):
        await aio_engine.find_one(PersonModel, True, False)


def test_sync_find_one_bad_query(sync_engine: SyncEngine):
    with pytest.raises(TypeError):
        sync_engine.find_one(PersonModel, True, False)


async def test_find_one_on_non_model(aio_engine: AIOEngine):
    class BadModel:
        pass

    with pytest.raises(TypeError):
        await aio_engine.find_one(BadModel)  # type: ignore


def test_sync_find_one_on_non_model(sync_engine: SyncEngine):
    class BadModel:
        pass

    with pytest.raises(TypeError):
        sync_engine.find_one(BadModel)  # type: ignore


async def test_find_invalid_limit(aio_engine: AIOEngine):
    with pytest.raises(ValueError):
        await aio_engine.find(PersonModel, limit=0)
    with pytest.raises(ValueError):
        await aio_engine.find(PersonModel, limit=-12)


def test_sync_find_invalid_limit(sync_engine: SyncEngine):
    with pytest.raises(ValueError):
        sync_engine.find(PersonModel, limit=0)
    with pytest.raises(ValueError):
        sync_engine.find(PersonModel, limit=-12)


async def test_find_invalid_skip(aio_engine: AIOEngine):
    with pytest.raises(ValueError):
        await aio_engine.find(PersonModel, skip=-1)
    with pytest.raises(ValueError):
        await aio_engine.find(PersonModel, limit=-12)


def test_sync_find_invalid_skip(sync_engine: SyncEngine):
    with pytest.raises(ValueError):
        sync_engine.find(PersonModel, skip=-1)
    with pytest.raises(ValueError):
        sync_engine.find(PersonModel, limit=-12)


@pytest.mark.usefixtures("person_persisted")
async def test_skip(aio_engine: AIOEngine):
    p = await aio_engine.find(PersonModel, skip=1)
    assert len(p) == 2


@pytest.mark.usefixtures("person_persisted")
def test_sync_skip(sync_engine: SyncEngine):
    p = list(sync_engine.find(PersonModel, skip=1))
    assert len(p) == 2


@pytest.mark.usefixtures("person_persisted")
async def test_limit(aio_engine: AIOEngine):
    p = await aio_engine.find(PersonModel, limit=1)
    assert len(p) == 1


@pytest.mark.usefixtures("person_persisted")
def test_sync_limit(sync_engine: SyncEngine):
    p = list(sync_engine.find(PersonModel, limit=1))
    assert len(p) == 1


@pytest.mark.usefixtures("person_persisted")
async def test_skip_limit(aio_engine: AIOEngine):
    p = await aio_engine.find(PersonModel, skip=1, limit=1)
    assert len(p) == 1


@pytest.mark.usefixtures("person_persisted")
def test_sync_skip_limit(sync_engine: SyncEngine):
    p = list(sync_engine.find(PersonModel, skip=1, limit=1))
    assert len(p) == 1


async def test_save_multiple_time_same_document(aio_engine: AIOEngine):
    fixed_id = ObjectId()

    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud", id=fixed_id)
    await aio_engine.save(instance)

    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud", id=fixed_id)
    await aio_engine.save(instance)

    assert await aio_engine.count(PersonModel, PersonModel.id == fixed_id) == 1


def test_sync_save_multiple_time_same_document(sync_engine: SyncEngine):
    fixed_id = ObjectId()

    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud", id=fixed_id)
    sync_engine.save(instance)

    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud", id=fixed_id)
    sync_engine.save(instance)

    assert sync_engine.count(PersonModel, PersonModel.id == fixed_id) == 1


@pytest.mark.usefixtures("person_persisted")
async def test_count(aio_engine: AIOEngine):
    count = await aio_engine.count(PersonModel)
    assert count == 3

    count = await aio_engine.count(PersonModel, PersonModel.first_name == "Michel")
    assert count == 1

    count = await aio_engine.count(PersonModel, PersonModel.first_name == "Gérard")
    assert count == 0


@pytest.mark.usefixtures("person_persisted")
def test_sync_count(sync_engine: SyncEngine):
    count = sync_engine.count(PersonModel)
    assert count == 3

    count = sync_engine.count(PersonModel, PersonModel.first_name == "Michel")
    assert count == 1

    count = sync_engine.count(PersonModel, PersonModel.first_name == "Gérard")
    assert count == 0


async def test_count_on_non_model_fails(aio_engine: AIOEngine):
    class BadModel:
        pass

    with pytest.raises(TypeError):
        await aio_engine.count(BadModel)  # type: ignore


def test_sync_count_on_non_model_fails(sync_engine: SyncEngine):
    class BadModel:
        pass

    with pytest.raises(TypeError):
        sync_engine.count(BadModel)  # type: ignore


async def test_find_on_embedded_raises(aio_engine: AIOEngine):
    class BadModel(EmbeddedModel):
        field: int

    with pytest.raises(TypeError):
        await aio_engine.find(BadModel)  # type: ignore


def test_sync_find_on_embedded_raises(sync_engine: SyncEngine):
    class BadModel(EmbeddedModel):
        field: int

    with pytest.raises(TypeError):
        sync_engine.find(BadModel)  # type: ignore


async def test_save_on_embedded(aio_engine: AIOEngine):
    class BadModel(EmbeddedModel):
        field: int

    instance = BadModel(field=12)
    with pytest.raises(TypeError):
        await aio_engine.save(instance)  # type: ignore


def test_sync_save_on_embedded(sync_engine: SyncEngine):
    class BadModel(EmbeddedModel):
        field: int

    instance = BadModel(field=12)
    with pytest.raises(TypeError):
        sync_engine.save(instance)  # type: ignore


@pytest.mark.usefixtures("person_persisted")
async def test_implicit_and(aio_engine: AIOEngine):
    count = await aio_engine.count(
        PersonModel,
        PersonModel.first_name == "Michel",
        PersonModel.last_name == "Drucker",
    )
    assert count == 1


@pytest.mark.usefixtures("person_persisted")
def test_sync_implicit_and(sync_engine: SyncEngine):
    count = sync_engine.count(
        PersonModel,
        PersonModel.first_name == "Michel",
        PersonModel.last_name == "Drucker",
    )
    assert count == 1


async def test_save_update(aio_engine: AIOEngine):
    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    await aio_engine.save(instance)
    assert await aio_engine.count(PersonModel, PersonModel.last_name == "Pernaud") == 1
    instance.last_name = "Dupuis"
    await aio_engine.save(instance)
    assert await aio_engine.count(PersonModel, PersonModel.last_name == "Pernaud") == 0
    assert await aio_engine.count(PersonModel, PersonModel.last_name == "Dupuis") == 1


def test_sync_save_update(sync_engine: SyncEngine):
    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    sync_engine.save(instance)
    assert sync_engine.count(PersonModel, PersonModel.last_name == "Pernaud") == 1
    instance.last_name = "Dupuis"
    sync_engine.save(instance)
    assert sync_engine.count(PersonModel, PersonModel.last_name == "Pernaud") == 0
    assert sync_engine.count(PersonModel, PersonModel.last_name == "Dupuis") == 1


async def test_delete_and_count(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    await aio_engine.delete(person_persisted[0])
    assert await aio_engine.count(PersonModel) == 2
    await aio_engine.delete(person_persisted[1])
    assert await aio_engine.count(PersonModel) == 1
    await aio_engine.delete(person_persisted[2])
    assert await aio_engine.count(PersonModel) == 0


def test_sync_delete_and_count(
    sync_engine: SyncEngine, person_persisted: List[PersonModel]
):
    sync_engine.delete(person_persisted[0])
    assert sync_engine.count(PersonModel) == 2
    sync_engine.delete(person_persisted[1])
    assert sync_engine.count(PersonModel) == 1
    sync_engine.delete(person_persisted[2])
    assert sync_engine.count(PersonModel) == 0


async def test_delete_not_existing(aio_engine: AIOEngine):
    non_persisted_instance = PersonModel(first_name="Jean", last_name="Paul")
    with pytest.raises(DocumentNotFoundError) as exc:
        await aio_engine.delete(non_persisted_instance)
    assert exc.value.instance == non_persisted_instance


def test_sync_delete_not_existing(sync_engine: SyncEngine):
    non_persisted_instance = PersonModel(first_name="Jean", last_name="Paul")
    with pytest.raises(DocumentNotFoundError) as exc:
        sync_engine.delete(non_persisted_instance)
    assert exc.value.instance == non_persisted_instance


@pytest.mark.usefixtures("person_persisted")
async def test_remove_and_count(aio_engine: AIOEngine):
    actual_delete_count = await aio_engine.remove(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )
    assert actual_delete_count == 2
    assert await aio_engine.count(PersonModel) == 1


@pytest.mark.usefixtures("person_persisted")
def test_sync_remove_and_count(sync_engine: SyncEngine):
    actual_delete_count = sync_engine.remove(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )
    assert actual_delete_count == 2
    assert sync_engine.count(PersonModel) == 1


@pytest.mark.usefixtures("person_persisted")
async def test_remove_just_one(aio_engine: AIOEngine):
    actual_delete_count = await aio_engine.remove(
        PersonModel, PersonModel.first_name == "Jean-Pierre", just_one=True
    )
    assert actual_delete_count == 1
    assert await aio_engine.count(PersonModel) == 2


@pytest.mark.usefixtures("person_persisted")
def test_sync_remove_just_one(sync_engine: SyncEngine):
    actual_delete_count = sync_engine.remove(
        PersonModel, PersonModel.first_name == "Jean-Pierre", just_one=True
    )
    assert actual_delete_count == 1
    assert sync_engine.count(PersonModel) == 2


@only_on_replica
@pytest.mark.usefixtures("person_persisted")
async def test_remove_just_one_transaction(aio_engine: AIOEngine):
    async with await aio_engine.client.start_session() as session:
        async with session.start_transaction():
            actual_delete_count = await aio_engine.remove(
                PersonModel,
                PersonModel.first_name == "Jean-Pierre",
                just_one=True,
                session=session,
            )
    assert actual_delete_count == 1
    assert await aio_engine.count(PersonModel) == 2


@only_on_replica
@pytest.mark.usefixtures("person_persisted")
def test_sync_remove_just_one_transaction(sync_engine: SyncEngine):
    with sync_engine.client.start_session() as session:
        with session.start_transaction():
            actual_delete_count = sync_engine.remove(
                PersonModel,
                PersonModel.first_name == "Jean-Pierre",
                just_one=True,
                session=session,
            )
    assert actual_delete_count == 1
    assert sync_engine.count(PersonModel) == 2


@only_on_replica
@pytest.mark.usefixtures("person_persisted")
async def test_remove_transaction_failure(aio_engine: AIOEngine):
    with pytest.raises(Exception):
        async with await aio_engine.client.start_session() as session:
            async with session.start_transaction():
                await aio_engine.remove(
                    PersonModel,
                    PersonModel.first_name == "Jean-Pierre",
                    session=session,
                )
                raise Exception("oops")
    assert await aio_engine.count(PersonModel) == 3  # type: ignore # (unreachable)


@only_on_replica
@pytest.mark.usefixtures("person_persisted")
def test_sync_remove_transaction_failure(sync_engine: SyncEngine):
    with pytest.raises(Exception):
        with sync_engine.client.start_session() as session:
            with session.start_transaction():
                sync_engine.remove(
                    PersonModel,
                    PersonModel.first_name == "Jean-Pierre",
                    session=session,
                )
                raise Exception("oops")
    assert sync_engine.count(PersonModel) == 3  # type: ignore # (unreachable)


@pytest.mark.usefixtures("person_persisted")
async def test_remove_not_existing(aio_engine: AIOEngine):
    instance = await aio_engine.find_one(
        PersonModel, PersonModel.last_name == "NotInDatabase"
    )
    assert instance is None
    deleted_count = await aio_engine.remove(
        PersonModel, PersonModel.last_name == "NotInDatabase"
    )
    assert deleted_count == 0


@pytest.mark.usefixtures("person_persisted")
def test_sync_remove_not_existing(sync_engine: SyncEngine):
    instance = sync_engine.find_one(
        PersonModel, PersonModel.last_name == "NotInDatabase"
    )
    assert instance is None
    deleted_count = sync_engine.remove(
        PersonModel, PersonModel.last_name == "NotInDatabase"
    )
    assert deleted_count == 0


async def test_modified_fields_cleared_on_document_saved(aio_engine: AIOEngine):
    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    assert len(instance.__fields_modified__) > 0
    await aio_engine.save(instance)
    assert len(instance.__fields_modified__) == 0


def test_sync_modified_fields_cleared_on_document_saved(sync_engine: SyncEngine):
    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    assert len(instance.__fields_modified__) > 0
    sync_engine.save(instance)
    assert len(instance.__fields_modified__) == 0


async def test_modified_fields_cleared_on_nested_document_saved(aio_engine: AIOEngine):
    hachette = Publisher(name="Hachette Livre", founded=1826, location="FR")
    book = Book(title="They Didn't See Us Coming", pages=304, publisher=hachette)
    assert len(hachette.__fields_modified__) > 0
    await aio_engine.save(book)
    assert len(hachette.__fields_modified__) == 0


def test_sync_modified_fields_cleared_on_nested_document_saved(sync_engine: SyncEngine):
    hachette = Publisher(name="Hachette Livre", founded=1826, location="FR")
    book = Book(title="They Didn't See Us Coming", pages=304, publisher=hachette)
    assert len(hachette.__fields_modified__) > 0
    sync_engine.save(book)
    assert len(hachette.__fields_modified__) == 0


@pytest.fixture()
async def engine_one_person(aio_engine: AIOEngine):
    await aio_engine.save(PersonModel(first_name="Jean-Pierre", last_name="Pernaud"))


@pytest.mark.usefixtures("engine_one_person")
async def test_modified_fields_on_find(aio_engine: AIOEngine):
    instance = await aio_engine.find_one(PersonModel)
    assert instance is not None
    assert len(instance.__fields_modified__) == 0


@pytest.mark.usefixtures("engine_one_person")
def test_sync_modified_fields_on_find(sync_engine: SyncEngine):
    instance = sync_engine.find_one(PersonModel)
    assert instance is not None
    assert len(instance.__fields_modified__) == 0


@pytest.mark.usefixtures("engine_one_person")
async def test_modified_fields_on_document_change(aio_engine: AIOEngine):
    instance = await aio_engine.find_one(PersonModel)
    assert instance is not None
    instance.first_name = "Jackie"
    assert len(instance.__fields_modified__) == 1
    instance.last_name = "Chan"
    assert len(instance.__fields_modified__) == 2


@pytest.mark.usefixtures("engine_one_person")
def test_sync_modified_fields_on_document_change(sync_engine: SyncEngine):
    instance = sync_engine.find_one(PersonModel)
    assert instance is not None
    instance.first_name = "Jackie"
    assert len(instance.__fields_modified__) == 1
    instance.last_name = "Chan"
    assert len(instance.__fields_modified__) == 2


@pytest.mark.usefixtures("engine_one_person")
async def test_no_set_on_save_fetched_document(
    aio_engine: AIOEngine, sync_mock_collection
):
    instance = await aio_engine.find_one(PersonModel)
    assert instance is not None

    collection = sync_mock_collection()
    await aio_engine.save(instance)
    collection.update_one.assert_not_called()


@pytest.mark.usefixtures("engine_one_person")
def test_sync_no_set_on_save_fetched_document(
    sync_engine: SyncEngine, sync_mock_collection
):
    instance = sync_engine.find_one(PersonModel)
    assert instance is not None

    collection = sync_mock_collection()
    sync_engine.save(instance)
    collection.update_one.assert_not_called()


@pytest.mark.usefixtures("engine_one_person")
async def test_only_modified_set_on_save(aio_engine: AIOEngine, aio_mock_collection):
    instance = await aio_engine.find_one(PersonModel)
    assert instance is not None

    instance.first_name = "John"
    collection = aio_mock_collection()
    await aio_engine.save(instance)
    collection.update_one.assert_awaited_once()
    (_, set_arg), _ = collection.update_one.await_args
    assert set_arg == {"$set": {"first_name": "John"}}


@pytest.mark.usefixtures("engine_one_person")
def test_sync_only_modified_set_on_save(sync_engine: SyncEngine, sync_mock_collection):
    instance = sync_engine.find_one(PersonModel)
    assert instance is not None

    instance.first_name = "John"
    collection = sync_mock_collection()
    sync_engine.save(instance)
    collection.update_one.assert_called_once()
    (_, set_arg), _ = collection.update_one.call_args
    assert set_arg == {"$set": {"first_name": "John"}}


async def test_only_mutable_list_set_on_save(
    aio_engine: AIOEngine, aio_mock_collection
):
    class M(Model):
        field: List[str]
        immutable_field: int

    instance = M(field=["hello"], immutable_field=12)
    await aio_engine.save(instance)

    collection = aio_mock_collection()
    await aio_engine.save(instance)
    collection.update_one.assert_awaited_once()
    (_, set_arg), _ = collection.update_one.await_args
    set_dict = set_arg["$set"]
    assert list(set_dict.keys()) == ["field"]


def test_sync_only_mutable_list_set_on_save(
    sync_engine: SyncEngine, sync_mock_collection
):
    class M(Model):
        field: List[str]
        immutable_field: int

    instance = M(field=["hello"], immutable_field=12)
    sync_engine.save(instance)

    collection = sync_mock_collection()
    sync_engine.save(instance)
    collection.update_one.assert_called_once()
    (_, set_arg), _ = collection.update_one.call_args
    set_dict = set_arg["$set"]
    assert list(set_dict.keys()) == ["field"]


async def test_only_mutable_list_of_embedded_set_on_save(
    aio_engine: AIOEngine, aio_mock_collection
):
    class E(EmbeddedModel):
        a: str

    class M(Model):
        field: List[E]

    instance = M(field=[E(a="hello")])
    await aio_engine.save(instance)

    collection = aio_mock_collection()
    await aio_engine.save(instance)
    collection.update_one.assert_awaited_once()
    (_, set_arg), _ = collection.update_one.await_args
    set_dict = set_arg["$set"]
    assert set_dict == {"field": [{"a": "hello"}]}


def test_sync_only_mutable_list_of_embedded_set_on_save(
    sync_engine: SyncEngine, sync_mock_collection
):
    class E(EmbeddedModel):
        a: str

    class M(Model):
        field: List[E]

    instance = M(field=[E(a="hello")])
    sync_engine.save(instance)

    collection = sync_mock_collection()
    sync_engine.save(instance)
    collection.update_one.assert_called_once()
    (_, set_arg), _ = collection.update_one.call_args
    set_dict = set_arg["$set"]
    assert set_dict == {"field": [{"a": "hello"}]}


async def test_only_mutable_dict_of_embedded_set_on_save(
    aio_engine: AIOEngine, aio_mock_collection
):
    class E(EmbeddedModel):
        a: str

    class M(Model):
        field: Dict[str, E]

    instance = M(field={"hello": E(a="world")})
    await aio_engine.save(instance)

    collection = aio_mock_collection()
    await aio_engine.save(instance)
    collection.update_one.assert_awaited_once()
    (_, set_arg), _ = collection.update_one.await_args
    set_dict = set_arg["$set"]
    assert set_dict == {"field": {"hello": {"a": "world"}}}


def test_sync_only_mutable_dict_of_embedded_set_on_save(
    sync_engine: SyncEngine, sync_mock_collection
):
    class E(EmbeddedModel):
        a: str

    class M(Model):
        field: Dict[str, E]

    instance = M(field={"hello": E(a="world")})
    sync_engine.save(instance)

    collection = sync_mock_collection()
    sync_engine.save(instance)
    collection.update_one.assert_called_once()
    (_, set_arg), _ = collection.update_one.call_args
    set_dict = set_arg["$set"]
    assert set_dict == {"field": {"hello": {"a": "world"}}}


async def test_only_tuple_of_embedded_set_on_save(
    aio_engine: AIOEngine, aio_mock_collection
):
    class E(EmbeddedModel):
        a: str

    class M(Model):
        field: Tuple[E]

    instance = M(field=(E(a="world"),))
    await aio_engine.save(instance)

    collection = aio_mock_collection()
    await aio_engine.save(instance)
    collection.update_one.assert_awaited_once()
    (_, set_arg), _ = collection.update_one.await_args
    set_dict = set_arg["$set"]
    assert set_dict == {
        "field": [
            {"a": "world"},
        ]
    }


def test_sync_only_tuple_of_embedded_set_on_save(
    sync_engine: SyncEngine, sync_mock_collection
):
    class E(EmbeddedModel):
        a: str

    class M(Model):
        field: Tuple[E]

    instance = M(field=(E(a="world"),))
    sync_engine.save(instance)

    collection = sync_mock_collection()
    sync_engine.save(instance)
    collection.update_one.assert_called_once()
    (_, set_arg), _ = collection.update_one.call_args
    set_dict = set_arg["$set"]
    assert set_dict == {
        "field": [
            {"a": "world"},
        ]
    }


async def test_find_sort_asc(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    results = await aio_engine.find(PersonModel, sort=PersonModel.last_name)
    assert results == sorted(person_persisted, key=lambda person: person.last_name)


def test_sync_find_sort_asc(
    sync_engine: SyncEngine, person_persisted: List[PersonModel]
):
    results = list(sync_engine.find(PersonModel, sort=PersonModel.last_name))
    assert results == sorted(person_persisted, key=lambda person: person.last_name)


async def test_find_sort_list(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    results = await aio_engine.find(
        PersonModel, sort=(PersonModel.first_name, PersonModel.last_name)
    )
    assert results == sorted(
        person_persisted, key=lambda person: (person.first_name, person.last_name)
    )


def test_sync_find_sort_list(
    sync_engine: SyncEngine, person_persisted: List[PersonModel]
):
    results = list(
        sync_engine.find(
            PersonModel, sort=(PersonModel.first_name, PersonModel.last_name)
        )
    )
    assert results == sorted(
        person_persisted, key=lambda person: (person.first_name, person.last_name)
    )


async def test_find_sort_wrong_argument(aio_engine: AIOEngine):
    with pytest.raises(
        TypeError,
        match=(
            "sort has to be a Model field or "
            "asc, desc descriptors or a tuple of these"
        ),
    ):
        await aio_engine.find(PersonModel, sort="first_name")


def test_sync_find_sort_wrong_argument(sync_engine: SyncEngine):
    with pytest.raises(
        TypeError,
        match=(
            "sort has to be a Model field or "
            "asc, desc descriptors or a tuple of these"
        ),
    ):
        sync_engine.find(PersonModel, sort="first_name")


async def test_find_sort_wrong_tuple_argument(aio_engine: AIOEngine):
    with pytest.raises(
        TypeError,
        match="sort elements have to be Model fields or asc, desc descriptors",
    ):
        await aio_engine.find(PersonModel, sort=("first_name",))


def test_sync_find_sort_wrong_tuple_argument(sync_engine: SyncEngine):
    with pytest.raises(
        TypeError,
        match="sort elements have to be Model fields or asc, desc descriptors",
    ):
        sync_engine.find(PersonModel, sort=("first_name",))


async def test_find_sort_desc(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    results = await aio_engine.find(
        PersonModel,
        sort=PersonModel.last_name.desc(),  # type: ignore
    )
    assert results == list(
        reversed(sorted(person_persisted, key=lambda person: person.last_name))
    )


def test_sync_find_sort_desc(
    sync_engine: SyncEngine, person_persisted: List[PersonModel]
):
    results = list(
        sync_engine.find(PersonModel, sort=PersonModel.last_name.desc())  # type: ignore
    )
    assert results == list(
        reversed(sorted(person_persisted, key=lambda person: person.last_name))
    )


async def test_find_sort_asc_function(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    results = await aio_engine.find(PersonModel, sort=asc(PersonModel.last_name))
    assert results == sorted(person_persisted, key=lambda person: person.last_name)


def test_sync_find_sort_asc_function(
    sync_engine: SyncEngine, person_persisted: List[PersonModel]
):
    results = list(sync_engine.find(PersonModel, sort=asc(PersonModel.last_name)))
    assert results == sorted(person_persisted, key=lambda person: person.last_name)


async def test_find_sort_multiple_descriptors(aio_engine: AIOEngine):
    class TestModel(Model):
        a: int
        b: int
        c: int

    persisted_models = [
        TestModel(a=1, b=2, c=3),
        TestModel(a=2, b=2, c=3),
        TestModel(a=3, b=3, c=2),
    ]
    await aio_engine.save_all(persisted_models)
    results = await aio_engine.find(
        TestModel,
        sort=(
            desc(TestModel.a),
            TestModel.b,
            TestModel.c.asc(),  # type: ignore
        ),
    )
    assert results == sorted(
        persisted_models,
        key=lambda test_model: (-test_model.a, test_model.b, test_model.c),
    )


def test_sync_find_sort_multiple_descriptors(sync_engine: SyncEngine):
    class TestModel(Model):
        a: int
        b: int
        c: int

    persisted_models = [
        TestModel(a=1, b=2, c=3),
        TestModel(a=2, b=2, c=3),
        TestModel(a=3, b=3, c=2),
    ]
    sync_engine.save_all(persisted_models)
    results = list(
        sync_engine.find(
            TestModel,
            sort=(
                desc(TestModel.a),
                TestModel.b,
                TestModel.c.asc(),  # type: ignore
            ),
        )
    )
    assert results == sorted(
        persisted_models,
        key=lambda test_model: (-test_model.a, test_model.b, test_model.c),
    )


async def test_sort_embedded_field(aio_engine: AIOEngine):
    class E(EmbeddedModel):
        field: int

    class M(Model):
        e: E

    instances = [M(e=E(field=0)), M(e=E(field=1)), M(e=E(field=2))]
    await aio_engine.save_all(instances)
    results = await aio_engine.find(M, sort=desc(M.e.field))
    assert results == sorted(instances, key=lambda instance: -instance.e.field)


def test_sync_sort_embedded_field(sync_engine: SyncEngine):
    class E(EmbeddedModel):
        field: int

    class M(Model):
        e: E

    instances = [M(e=E(field=0)), M(e=E(field=1)), M(e=E(field=2))]
    sync_engine.save_all(instances)
    results = list(sync_engine.find(M, sort=desc(M.e.field)))
    assert results == sorted(instances, key=lambda instance: -instance.e.field)


async def test_find_one_sort(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    person = await aio_engine.find_one(PersonModel, sort=PersonModel.last_name)
    assert person is not None
    assert person.last_name == "Castaldi"


def test_sync_find_one_sort(
    sync_engine: SyncEngine, person_persisted: List[PersonModel]
):
    person = sync_engine.find_one(PersonModel, sort=PersonModel.last_name)
    assert person is not None
    assert person.last_name == "Castaldi"


async def test_find_document_field_not_set_with_default(aio_engine: AIOEngine):
    class M(Model):
        field: Optional[str] = None

    await aio_engine.get_collection(M).insert_one({"_id": ObjectId()})
    gathered = await aio_engine.find_one(M)
    assert gathered is not None
    assert gathered.field is None


def test_sync_find_document_field_not_set_with_default(sync_engine: SyncEngine):
    class M(Model):
        field: Optional[str] = None

    sync_engine.get_collection(M).insert_one({"_id": ObjectId()})
    gathered = sync_engine.find_one(M)
    assert gathered is not None
    assert gathered.field is None


async def test_find_document_field_not_set_with_default_field_descriptor(
    aio_engine: AIOEngine,
):
    class M(Model):
        field: str = Field(default="hello world")

    await aio_engine.get_collection(M).insert_one({"_id": ObjectId()})
    gathered = await aio_engine.find_one(M)
    assert gathered is not None
    assert gathered.field == "hello world"


def test_sync_find_document_field_not_set_with_default_field_descriptor(
    sync_engine: SyncEngine,
):
    class M(Model):
        field: str = Field(default="hello world")

    sync_engine.get_collection(M).insert_one({"_id": ObjectId()})
    gathered = sync_engine.find_one(M)
    assert gathered is not None
    assert gathered.field == "hello world"


async def test_find_document_field_not_set_with_no_default(aio_engine: AIOEngine):
    class M(Model):
        field: str

    oid = ObjectId()
    await aio_engine.get_collection(M).insert_one({"_id": oid})
    with pytest.raises(DocumentParsingError) as exc_info:
        await aio_engine.find_one(M)
    assert redact_objectid(str(exc_info.value), oid) == snapshot(
        """\
1 validation error for M
field
  Key 'field' not found in document [type=odmantic::key_not_found_in_document, input_value={'_id': ObjectId('<ObjectId>')}, input_type=dict]\
"""  # noqa: E501
    )


def test_sync_find_document_field_not_set_with_no_default(sync_engine: SyncEngine):
    class M(Model):
        field: str

    oid = ObjectId()
    sync_engine.get_collection(M).insert_one({"_id": oid})
    with pytest.raises(DocumentParsingError) as exc_info:
        sync_engine.find_one(M)

    assert redact_objectid(str(exc_info.value), oid) == snapshot(
        """\
1 validation error for M
field
  Key 'field' not found in document [type=odmantic::key_not_found_in_document, input_value={'_id': ObjectId('<ObjectId>')}, input_type=dict]\
"""  # noqa: E501
    )


async def test_find_document_field_not_set_with_default_factory_disabled(
    aio_engine: AIOEngine,
):
    class M(Model):
        field: str = Field(default_factory=lambda: "hello")  # pragma: no cover

    await aio_engine.get_collection(M).insert_one({"_id": ObjectId()})
    with pytest.raises(DocumentParsingError, match="Key 'field' not found in document"):
        await aio_engine.find_one(M)


def test_sync_find_document_field_not_set_with_default_factory_disabled(
    sync_engine: SyncEngine,
):
    class M(Model):
        field: str = Field(default_factory=lambda: "hello")  # pragma: no cover

    sync_engine.get_collection(M).insert_one({"_id": ObjectId()})
    with pytest.raises(DocumentParsingError, match="Key 'field' not found in document"):
        sync_engine.find_one(M)


async def test_find_document_field_not_set_with_default_factory_enabled(
    aio_engine: AIOEngine,
):
    class M(Model):
        field: str = Field(default_factory=lambda: "hello")

        model_config = {"parse_doc_with_default_factories": True}

    await aio_engine.get_collection(M).insert_one({"_id": ObjectId()})
    instance = await aio_engine.find_one(M)
    assert instance is not None
    assert instance.field == "hello"


def test_sync_find_document_field_not_set_with_default_factory_enabled(
    sync_engine: SyncEngine,
):
    class M(Model):
        field: str = Field(default_factory=lambda: "hello")

        model_config = {
            "parse_doc_with_default_factories": True,
        }

    sync_engine.get_collection(M).insert_one({"_id": ObjectId()})
    instance = sync_engine.find_one(M)
    assert instance is not None
    assert instance.field == "hello"
