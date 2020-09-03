import pytest

from odmantic.engine import AIOEngine
from odmantic.model import EmbeddedModel, Model

from ..zoo.book_embedded import Book, Publisher
from ..zoo.patron_embedded import Address, Patron

pytestmark = pytest.mark.asyncio


async def test_add_fetch_single(engine: AIOEngine):
    publisher = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    book = Book(title="MongoDB: The Definitive Guide", pages=216, publisher=publisher)
    instance = await engine.add(book)
    assert instance.id is not None
    assert isinstance(instance.publisher, Publisher)
    assert instance.publisher == publisher

    fetched_instance = await engine.find_one(Book, Book.id == instance.id)
    assert fetched_instance is not None
    assert fetched_instance.publisher == publisher


async def test_add_multiple(engine: AIOEngine):
    addresses = [
        Address(street="81 Lafayette St.", city="Brownsburg", state="IN", zip="46112"),
        Address(
            street="862 West Euclid St.", city="Indian Trail", state="NC", zip="28079"
        ),
    ]
    patron = Patron(name="The Princess Royal", addresses=addresses)
    instance = await engine.add(patron)
    assert instance.id is not None
    assert isinstance(instance.addresses, list)
    assert instance.addresses == addresses

    fetched_instance = await engine.find_one(Patron)
    assert fetched_instance is not None
    assert fetched_instance.addresses == addresses


@pytest.mark.skip("Not supported yet")
async def test_query_filter_on_embedded_doc(engine: AIOEngine):
    publisher_1 = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    book_1 = Book(
        title="MongoDB: The Definitive Guide", pages=216, publisher=publisher_1
    )
    publisher_2 = Publisher(name="O'Reilly Media", founded=2020, location="EU")
    book_2 = Book(title="MySQL: The Definitive Guide", pages=516, publisher=publisher_2)
    instance_1, instance_2 = await engine.add_all([book_1, book_2])
    fetched_instances = await engine.find(Book, Book.publisher == publisher_2)
    assert len(fetched_instances) == 1
    assert fetched_instances[0] == book_2


@pytest.mark.skip("Not supported yet")
async def test_query_filter_on_embedded_field(engine: AIOEngine):
    publisher_1 = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    book_1 = Book(
        title="MongoDB: The Definitive Guide", pages=216, publisher=publisher_1
    )
    publisher_2 = Publisher(name="O'Reilly Media", founded=2020, location="EU")
    book_2 = Book(title="MySQL: The Definitive Guide", pages=516, publisher=publisher_2)
    instance_1, instance_2 = await engine.add_all([book_1, book_2])
    fetched_instances = await engine.find(Book, Book.publisher.location == "EU")
    assert len(fetched_instances) == 1
    assert fetched_instances[0] == book_2


@pytest.mark.skip("Not supported yet")
async def test_query_filter_on_embedded_nested(engine: AIOEngine):
    class ThirdModel(EmbeddedModel):
        field: int

    class SecondaryModel(EmbeddedModel):
        nested_1: ThirdModel

    class TopModel(Model):
        nested_0: SecondaryModel

    instance_0 = TopModel(nested_0=SecondaryModel(nested_1=ThirdModel(field=12)))
    instance_1 = TopModel(nested_0=SecondaryModel(nested_1=ThirdModel(field=0)))
    await engine.add_all([instance_0, instance_1])

    fetched_instances = await engine.find(
        TopModel, TopModel.nested_0.nested_1.field == 12
    )

    assert len(fetched_instances) == 1
    assert fetched_instances[0] == instance_0
