import pytest

from odmantic.engine import AIOEngine
from tests.zoo.deeply_nested import NestedLevel1, NestedLevel2, NestedLevel3

from ..zoo.book_reference import Book, Publisher

pytestmark = pytest.mark.asyncio


async def test_add_with_references(engine: AIOEngine):
    publisher = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    book = Book(title="MongoDB: The Definitive Guide", pages=216, publisher=publisher)
    instance = await engine.save(book)
    fetched_subinstance = await engine.find_one(
        Publisher, Publisher.id == instance.publisher.id
    )
    assert fetched_subinstance == publisher


# TODO Handle the case where the referenced object already exists

# TODO test add with duplicated reference id


async def test_save_deeply_nested(engine: AIOEngine):
    instance = NestedLevel1(next_=NestedLevel2(next_=NestedLevel3()))
    await engine.save(instance)
    assert await engine.count(NestedLevel3) == 1
    assert await engine.count(NestedLevel2) == 1
    assert await engine.count(NestedLevel1) == 1


async def test_update_deeply_nested(engine: AIOEngine):
    inst3 = NestedLevel3(field=0)
    instance = NestedLevel1(next_=NestedLevel2(next_=inst3))
    await engine.save(instance)
    assert await engine.count(NestedLevel3, NestedLevel3.field == 42) == 0
    # instance.next_.next_.field = 42
    inst3.field = 42
    await engine.save(instance)
    assert await engine.count(NestedLevel3, NestedLevel3.field == 42) == 1
