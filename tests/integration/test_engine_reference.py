import pytest

from odmantic.bson import ObjectId
from odmantic.engine import AIOEngine
from odmantic.exceptions import DocumentParsingError
from odmantic.model import Model
from odmantic.reference import Reference
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
    inst3 = NestedLevel3(
        field=0
    )  # Isolate inst3 to make sure it's not internaly copied
    instance = NestedLevel1(next_=NestedLevel2(next_=inst3))
    await engine.save(instance)
    assert await engine.count(NestedLevel3, NestedLevel3.field == 42) == 0
    inst3.field = 42
    await engine.save(instance)
    assert await engine.count(NestedLevel3, NestedLevel3.field == 42) == 1


async def test_save_deeply_nested_and_fetch(engine: AIOEngine):
    instance = NestedLevel1(next_=NestedLevel2(next_=NestedLevel3(field=0)))
    await engine.save(instance)

    fetched = await engine.find_one(NestedLevel1)
    assert fetched == instance


async def test_multiple_save_deeply_nested_and_fetch(engine: AIOEngine):
    instances = [
        NestedLevel1(field=1, next_=NestedLevel2(field=2, next_=NestedLevel3(field=3))),
        NestedLevel1(field=4, next_=NestedLevel2(field=5, next_=NestedLevel3(field=6))),
    ]
    await engine.save_all(instances)

    fetched = await engine.find(NestedLevel1)
    assert len(fetched) == 2
    assert fetched[0] in instances
    assert fetched[1] in instances


async def test_reference_with_key_name(engine: AIOEngine):
    class R(Model):
        field: int

    class M(Model):
        r: R = Reference(key_name="fancy_key_name")

    instance = M(r=R(field=3))
    assert "fancy_key_name" in instance.doc()
    await engine.save(instance)

    fetched = await engine.find_one(M)
    assert fetched is not None
    assert fetched.r.field == 3


async def test_reference_not_set_in_database(engine: AIOEngine):
    class R(Model):
        field: int

    class M(Model):
        r: R = Reference()

    await engine.get_collection(M).insert_one({"_id": ObjectId()})
    with pytest.raises(DocumentParsingError, match="field required"):
        await engine.find_one(M)
