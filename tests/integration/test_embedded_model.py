from typing import Dict, List, Tuple

import pytest

from odmantic.engine import AIOEngine, SyncEngine
from odmantic.field import Field
from odmantic.model import EmbeddedModel, Model

from ..zoo.book_embedded import Book, Publisher
from ..zoo.patron_embedded import Address, Patron

pytestmark = pytest.mark.asyncio


async def test_add_fetch_single(aio_engine: AIOEngine):
    publisher = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    book = Book(title="MongoDB: The Definitive Guide", pages=216, publisher=publisher)
    instance = await aio_engine.save(book)
    assert instance.id is not None
    assert isinstance(instance.publisher, Publisher)
    assert instance.publisher == publisher

    fetched_instance = await aio_engine.find_one(Book, Book.id == instance.id)
    assert fetched_instance is not None
    assert fetched_instance.publisher == publisher


def test_sync_add_fetch_single(sync_engine: SyncEngine):
    publisher = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    book = Book(title="MongoDB: The Definitive Guide", pages=216, publisher=publisher)
    instance = sync_engine.save(book)
    assert instance.id is not None
    assert isinstance(instance.publisher, Publisher)
    assert instance.publisher == publisher

    fetched_instance = sync_engine.find_one(Book, Book.id == instance.id)
    assert fetched_instance is not None
    assert fetched_instance.publisher == publisher


async def test_add_multiple(aio_engine: AIOEngine):
    addresses = [
        Address(street="81 Lafayette St.", city="Brownsburg", state="IN", zip="46112"),
        Address(
            street="862 West Euclid St.", city="Indian Trail", state="NC", zip="28079"
        ),
    ]
    patron = Patron(name="The Princess Royal", addresses=addresses)
    instance = await aio_engine.save(patron)
    assert instance.id is not None
    assert isinstance(instance.addresses, list)
    assert instance.addresses == addresses

    fetched_instance = await aio_engine.find_one(Patron)
    assert fetched_instance is not None
    assert fetched_instance.addresses == addresses


def test_sync_add_multiple(sync_engine: SyncEngine):
    addresses = [
        Address(street="81 Lafayette St.", city="Brownsburg", state="IN", zip="46112"),
        Address(
            street="862 West Euclid St.", city="Indian Trail", state="NC", zip="28079"
        ),
    ]
    patron = Patron(name="The Princess Royal", addresses=addresses)
    instance = sync_engine.save(patron)
    assert instance.id is not None
    assert isinstance(instance.addresses, list)
    assert instance.addresses == addresses

    fetched_instance = sync_engine.find_one(Patron)
    assert fetched_instance is not None
    assert fetched_instance.addresses == addresses


@pytest.fixture
async def books_with_embedded_publisher(aio_engine: AIOEngine):
    publisher_1 = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    book_1 = Book(
        title="MongoDB: The Definitive Guide", pages=216, publisher=publisher_1
    )
    publisher_2 = Publisher(name="O'Reilly Media", founded=2020, location="EU")
    book_2 = Book(title="MySQL: The Definitive Guide", pages=516, publisher=publisher_2)
    return await aio_engine.save_all([book_1, book_2])


async def test_query_filter_on_embedded_doc(
    aio_engine: AIOEngine, books_with_embedded_publisher: Tuple[Book, Book]
):
    _, book_2 = books_with_embedded_publisher
    fetched_instances = await aio_engine.find(Book, Book.publisher == book_2.publisher)
    assert len(fetched_instances) == 1
    assert fetched_instances[0] == book_2


def test_sync_query_filter_on_embedded_doc(
    sync_engine: SyncEngine, books_with_embedded_publisher: Tuple[Book, Book]
):
    _, book_2 = books_with_embedded_publisher
    fetched_instances = list(sync_engine.find(Book, Book.publisher == book_2.publisher))
    assert len(fetched_instances) == 1
    assert fetched_instances[0] == book_2


async def test_query_filter_on_embedded_field(
    aio_engine: AIOEngine, books_with_embedded_publisher: Tuple[Book, Book]
):
    _, book_2 = books_with_embedded_publisher
    fetched_instances = await aio_engine.find(Book, Book.publisher.location == "EU")
    assert len(fetched_instances) == 1
    assert fetched_instances[0] == book_2


def test_sync_query_filter_on_embedded_field(
    sync_engine: SyncEngine, books_with_embedded_publisher: Tuple[Book, Book]
):
    _, book_2 = books_with_embedded_publisher
    fetched_instances = list(sync_engine.find(Book, Book.publisher.location == "EU"))
    assert len(fetched_instances) == 1
    assert fetched_instances[0] == book_2


async def test_query_filter_on_embedded_nested(aio_engine: AIOEngine):
    class ThirdModel(EmbeddedModel):
        field: int

    class SecondaryModel(EmbeddedModel):
        nested_1: ThirdModel

    class TopModel(Model):
        nested_0: SecondaryModel

    instance_0 = TopModel(nested_0=SecondaryModel(nested_1=ThirdModel(field=12)))
    instance_1 = TopModel(nested_0=SecondaryModel(nested_1=ThirdModel(field=0)))
    await aio_engine.save_all([instance_0, instance_1])

    fetched_instances = await aio_engine.find(
        TopModel, TopModel.nested_0.nested_1.field == 12
    )

    assert len(fetched_instances) == 1
    assert fetched_instances[0] == instance_0


def test_sync_query_filter_on_embedded_nested(sync_engine: SyncEngine):
    class ThirdModel(EmbeddedModel):
        field: int

    class SecondaryModel(EmbeddedModel):
        nested_1: ThirdModel

    class TopModel(Model):
        nested_0: SecondaryModel

    instance_0 = TopModel(nested_0=SecondaryModel(nested_1=ThirdModel(field=12)))
    instance_1 = TopModel(nested_0=SecondaryModel(nested_1=ThirdModel(field=0)))
    sync_engine.save_all([instance_0, instance_1])

    fetched_instances = list(
        sync_engine.find(TopModel, TopModel.nested_0.nested_1.field == 12)
    )

    assert len(fetched_instances) == 1
    assert fetched_instances[0] == instance_0


async def test_fields_modified_embedded_model_modification(aio_engine: AIOEngine):
    class E(EmbeddedModel):
        f: int

    class M(Model):
        e: E

    e = E(f=0)
    m = M(e=e)
    await aio_engine.save(m)
    e.f = 1
    await aio_engine.save(m)
    fetched = await aio_engine.find_one(M)
    assert fetched is not None
    assert fetched.e.f == 1


def test_sync_fields_modified_embedded_model_modification(sync_engine: SyncEngine):
    class E(EmbeddedModel):
        f: int

    class M(Model):
        e: E

    e = E(f=0)
    m = M(e=e)
    sync_engine.save(m)
    e.f = 1
    sync_engine.save(m)
    fetched = sync_engine.find_one(M)
    assert fetched is not None
    assert fetched.e.f == 1


async def test_embedded_model_as_primary_field_named_id(aio_engine: AIOEngine):
    class Id(EmbeddedModel):
        user: int
        chat: int

    class User(Model):
        id: Id = Field(primary_field=True)

    user = User(id=Id(user=1, chat=1001))
    await aio_engine.save(user)
    assert (
        await aio_engine.find_one(User, User.id == Id(user=1, chat=1001))
    ) is not None


async def test_sync_embedded_model_as_primary_field_named_id(sync_engine: SyncEngine):
    class Id(EmbeddedModel):
        user: int
        chat: int

    class User(Model):
        id: Id = Field(primary_field=True)

    user = User(id=Id(user=1, chat=1001))
    sync_engine.save(user)
    assert sync_engine.find_one(User, User.id == Id(user=1, chat=1001)) is not None


async def test_embedded_model_custom_key_name_save_and_fetch(aio_engine: AIOEngine):
    class In(EmbeddedModel):
        a: int = Field(key_name="in-a")

    class Out(Model):
        inner: In = Field(key_name="in")

    instance = Out(inner=In(a=3))
    await aio_engine.save(instance)
    fetched = await aio_engine.find_one(Out)
    assert instance == fetched


def test_sync_embedded_model_custom_key_name_save_and_fetch(sync_engine: SyncEngine):
    class In(EmbeddedModel):
        a: int = Field(key_name="in-a")

    class Out(Model):
        inner: In = Field(key_name="in")

    instance = Out(inner=In(a=3))
    sync_engine.save(instance)
    fetched = sync_engine.find_one(Out)
    assert instance == fetched


async def test_embedded_model_list_custom_key_name_save_and_fetch(
    aio_engine: AIOEngine,
):
    class In(EmbeddedModel):
        a: int = Field(key_name="in-a")

    class Out(Model):
        inner: List[In] = Field(key_name="in")

    instance = Out(inner=[In(a=3)])
    await aio_engine.save(instance)
    fetched = await aio_engine.find_one(Out)
    assert instance == fetched


def test_sync_embedded_model_list_custom_key_name_save_and_fetch(
    sync_engine: SyncEngine,
):
    class In(EmbeddedModel):
        a: int = Field(key_name="in-a")

    class Out(Model):
        inner: List[In] = Field(key_name="in")

    instance = Out(inner=[In(a=3)])
    sync_engine.save(instance)
    fetched = sync_engine.find_one(Out)
    assert instance == fetched


async def test_embedded_model_dict_custom_key_name_save_and_fetch(
    aio_engine: AIOEngine,
):
    class In(EmbeddedModel):
        a: int = Field(key_name="in-a")

    class Out(Model):
        inner: Dict[str, In] = Field(key_name="in")

    instance = Out(inner={"key": In(a=3)})
    await aio_engine.save(instance)
    fetched = await aio_engine.find_one(Out)
    assert instance == fetched


def test_sync_embedded_model_dict_custom_key_name_save_and_fetch(
    sync_engine: SyncEngine,
):
    class In(EmbeddedModel):
        a: int = Field(key_name="in-a")

    class Out(Model):
        inner: Dict[str, In] = Field(key_name="in")

    instance = Out(inner={"key": In(a=3)})
    sync_engine.save(instance)
    fetched = sync_engine.find_one(Out)
    assert instance == fetched
