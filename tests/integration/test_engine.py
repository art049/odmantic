from typing import Dict, List, Optional, Tuple

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from odmantic.bson import ObjectId
from odmantic.engine import AIOEngine
from odmantic.exceptions import DocumentNotFoundError, DocumentParsingError
from odmantic.field import Field
from odmantic.model import EmbeddedModel, Model
from odmantic.query import asc, desc
from tests.zoo.book_reference import Book, Publisher

from ..zoo.person import PersonModel

pytestmark = pytest.mark.asyncio


async def test_default_motor_client_creation():
    engine = AIOEngine()
    assert isinstance(engine.client, AsyncIOMotorClient)


@pytest.mark.parametrize("illegal_character", ("/", "\\", ".", '"', "$"))
def test_invalid_database_name(illegal_character: str):
    with pytest.raises(ValueError, match="database name cannot contain"):
        AIOEngine(database=f"prefix{illegal_character}suffix")


async def test_save(aio_engine: AIOEngine):
    instance = await aio_engine.save(
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    )
    assert isinstance(instance.id, ObjectId)


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


async def test_find_one_not_existing(aio_engine: AIOEngine):
    fetched = await aio_engine.find_one(PersonModel)
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


async def test_find_sync_iteration(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    fetched = set()
    for inst in await aio_engine.find(PersonModel):
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


async def test_find_skip(aio_engine: AIOEngine, person_persisted: List[PersonModel]):
    results = await aio_engine.find(PersonModel, skip=1)
    assert len(results) == 2
    for instance in results:
        assert instance in person_persisted


async def test_find_one_bad_query(aio_engine: AIOEngine):
    with pytest.raises(TypeError):
        await aio_engine.find_one(PersonModel, True, False)


async def test_find_one_on_non_model(aio_engine: AIOEngine):
    class BadModel:
        pass

    with pytest.raises(TypeError):
        await aio_engine.find_one(BadModel)  # type: ignore


async def test_find_invalid_limit(aio_engine: AIOEngine):
    with pytest.raises(ValueError):
        await aio_engine.find(PersonModel, limit=0)
    with pytest.raises(ValueError):
        await aio_engine.find(PersonModel, limit=-12)


async def test_find_invalid_skip(aio_engine: AIOEngine):
    with pytest.raises(ValueError):
        await aio_engine.find(PersonModel, skip=-1)
    with pytest.raises(ValueError):
        await aio_engine.find(PersonModel, limit=-12)


@pytest.mark.usefixtures("person_persisted")
async def test_skip(aio_engine: AIOEngine):
    p = await aio_engine.find(PersonModel, skip=1)
    assert len(p) == 2


@pytest.mark.usefixtures("person_persisted")
async def test_limit(aio_engine: AIOEngine):
    p = await aio_engine.find(PersonModel, limit=1)
    assert len(p) == 1


@pytest.mark.usefixtures("person_persisted")
async def test_skip_limit(aio_engine: AIOEngine):
    p = await aio_engine.find(PersonModel, skip=1, limit=1)
    assert len(p) == 1


async def test_save_multiple_time_same_document(aio_engine: AIOEngine):
    fixed_id = ObjectId()

    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud", id=fixed_id)
    await aio_engine.save(instance)

    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud", id=fixed_id)
    await aio_engine.save(instance)

    assert await aio_engine.count(PersonModel, PersonModel.id == fixed_id) == 1


@pytest.mark.usefixtures("person_persisted")
async def test_count(aio_engine: AIOEngine):
    count = await aio_engine.count(PersonModel)
    assert count == 3

    count = await aio_engine.count(PersonModel, PersonModel.first_name == "Michel")
    assert count == 1

    count = await aio_engine.count(PersonModel, PersonModel.first_name == "Gérard")
    assert count == 0


async def test_count_on_non_model_fails(aio_engine: AIOEngine):
    class BadModel:
        pass

    with pytest.raises(TypeError):
        await aio_engine.count(BadModel)  # type: ignore


async def test_find_on_embedded_raises(aio_engine: AIOEngine):
    class BadModel(EmbeddedModel):
        field: int

    with pytest.raises(TypeError):
        await aio_engine.find(BadModel)  # type: ignore


async def test_save_on_embedded(aio_engine: AIOEngine):
    class BadModel(EmbeddedModel):
        field: int

    instance = BadModel(field=12)
    with pytest.raises(TypeError):
        await aio_engine.save(instance)  # type: ignore


@pytest.mark.usefixtures("person_persisted")
async def test_implicit_and(aio_engine: AIOEngine):
    count = await aio_engine.count(
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


async def test_delete_and_count(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    await aio_engine.delete(person_persisted[0])
    assert await aio_engine.count(PersonModel) == 2
    await aio_engine.delete(person_persisted[1])
    assert await aio_engine.count(PersonModel) == 1
    await aio_engine.delete(person_persisted[2])
    assert await aio_engine.count(PersonModel) == 0


async def test_delete_not_existing(aio_engine: AIOEngine):
    non_persisted_instance = PersonModel(first_name="Jean", last_name="Paul")
    with pytest.raises(DocumentNotFoundError) as exc:
        await aio_engine.delete(non_persisted_instance)
    assert exc.value.instance == non_persisted_instance


async def test_modified_fields_cleared_on_document_saved(aio_engine: AIOEngine):
    instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    assert len(instance.__fields_modified__) > 0
    await aio_engine.save(instance)
    assert len(instance.__fields_modified__) == 0


async def test_modified_fields_cleared_on_nested_document_saved(aio_engine: AIOEngine):
    hachette = Publisher(name="Hachette Livre", founded=1826, location="FR")
    book = Book(title="They Didn't See Us Coming", pages=304, publisher=hachette)
    assert len(hachette.__fields_modified__) > 0
    await aio_engine.save(book)
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
async def test_modified_fields_on_document_change(aio_engine: AIOEngine):
    instance = await aio_engine.find_one(PersonModel)
    assert instance is not None
    instance.first_name = "Jackie"
    assert len(instance.__fields_modified__) == 1
    instance.last_name = "Chan"
    assert len(instance.__fields_modified__) == 2


@pytest.mark.usefixtures("engine_one_person")
async def test_no_set_on_save_fetched_document(
    aio_engine: AIOEngine, aio_mock_collection
):
    instance = await aio_engine.find_one(PersonModel)
    assert instance is not None

    collection = aio_mock_collection()
    await aio_engine.save(instance)
    collection.update_one.assert_not_awaited()


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
    assert set_dict == {"field": ({"a": "world"},)}


async def test_find_sort_asc(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    results = await aio_engine.find(PersonModel, sort=PersonModel.last_name)
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


async def test_find_sort_wrong_argument(aio_engine: AIOEngine):
    with pytest.raises(
        TypeError,
        match=(
            "sort has to be a Model field or "
            "asc, desc descriptors or a tuple of these"
        ),
    ):
        await aio_engine.find(PersonModel, sort="first_name")


async def test_find_sort_wrong_tuple_argument(aio_engine: AIOEngine):
    with pytest.raises(
        TypeError,
        match="sort elements have to be Model fields or asc, desc descriptors",
    ):
        await aio_engine.find(PersonModel, sort=("first_name",))


async def test_find_sort_desc(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    results = await aio_engine.find(
        PersonModel, sort=PersonModel.last_name.desc()  # type: ignore
    )
    assert results == list(
        reversed(sorted(person_persisted, key=lambda person: person.last_name))
    )


async def test_find_sort_asc_function(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    results = await aio_engine.find(PersonModel, sort=asc(PersonModel.last_name))
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


async def test_sort_embedded_field(aio_engine: AIOEngine):
    class E(EmbeddedModel):
        field: int

    class M(Model):
        e: E

    instances = [M(e=E(field=0)), M(e=E(field=1)), M(e=E(field=2))]
    await aio_engine.save_all(instances)
    results = await aio_engine.find(M, sort=desc(M.e.field))
    assert results == sorted(instances, key=lambda instance: -instance.e.field)


async def test_find_one_sort(
    aio_engine: AIOEngine, person_persisted: List[PersonModel]
):
    person = await aio_engine.find_one(PersonModel, sort=PersonModel.last_name)
    assert person is not None
    assert person.last_name == "Castaldi"


async def test_find_document_field_not_set_with_default(aio_engine: AIOEngine):
    class M(Model):
        field: Optional[str] = None

    await aio_engine.get_collection(M).insert_one({"_id": ObjectId()})
    gathered = await aio_engine.find_one(M)
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


async def test_find_document_field_not_set_with_no_default(aio_engine: AIOEngine):
    class M(Model):
        field: str

    await aio_engine.get_collection(M).insert_one({"_id": ObjectId()})
    with pytest.raises(
        DocumentParsingError, match="key not found in document"
    ) as exc_info:
        await aio_engine.find_one(M)
    assert (
        "1 validation error for M\n"
        "field\n"
        "  key not found in document "
        "(type=value_error.keynotfoundindocument; key_name='field')"
    ) in str(exc_info.value)


async def test_find_document_field_not_set_with_default_factory_disabled(
    aio_engine: AIOEngine,
):
    class M(Model):
        field: str = Field(default_factory=lambda: "hello")  # pragma: no cover

    await aio_engine.get_collection(M).insert_one({"_id": ObjectId()})
    with pytest.raises(DocumentParsingError, match="key not found in document"):
        await aio_engine.find_one(M)


async def test_find_document_field_not_set_with_default_factory_enabled(
    aio_engine: AIOEngine,
):
    class M(Model):
        field: str = Field(default_factory=lambda: "hello")

        class Config:
            parse_doc_with_default_factories = True

    await aio_engine.get_collection(M).insert_one({"_id": ObjectId()})
    instance = await aio_engine.find_one(M)
    assert instance is not None
    assert instance.field == "hello"
