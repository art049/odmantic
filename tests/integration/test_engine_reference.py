import pytest

from odmantic.engine import AIOEngine

from ..zoo.book_reference import Book, Publisher

pytestmark = pytest.mark.asyncio


async def test_add_with_references(engine: AIOEngine):
    publisher = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    book = Book(title="MongoDB: The Definitive Guide", pages=216, publisher=publisher)
    instance = await engine.add(book)
    fetched_subinstance = await engine.find_one(
        Publisher, Publisher.id == instance.publisher.id
    )
    assert fetched_subinstance == publisher


# TODO Handle the case where the referenced object already exists

# TODO test add with duplicated reference id
