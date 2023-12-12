import pytest
from inline_snapshot import snapshot

from odmantic.bson import ObjectId
from odmantic.engine import AIOEngine, SyncEngine
from odmantic.exceptions import DocumentParsingError
from odmantic.model import Model
from odmantic.reference import Reference
from tests.integration.conftest import only_on_replica
from tests.integration.utils import redact_objectid
from tests.zoo.deeply_nested import NestedLevel1, NestedLevel2, NestedLevel3

from ..zoo.book_reference import Book, Publisher

pytestmark = pytest.mark.asyncio


async def test_add_with_references(aio_engine: AIOEngine):
    publisher = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    book = Book(title="MongoDB: The Definitive Guide", pages=216, publisher=publisher)
    instance = await aio_engine.save(book)
    fetched_subinstance = await aio_engine.find_one(
        Publisher, Publisher.id == instance.publisher.id
    )
    assert fetched_subinstance == publisher


def test_sync_add_with_references(sync_engine: SyncEngine):
    publisher = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    book = Book(title="MongoDB: The Definitive Guide", pages=216, publisher=publisher)
    instance = sync_engine.save(book)
    fetched_subinstance = sync_engine.find_one(
        Publisher, Publisher.id == instance.publisher.id
    )
    assert fetched_subinstance == publisher


# TODO Handle the case where the referenced object already exists

# TODO test add with duplicated reference id


async def test_save_deeply_nested(aio_engine: AIOEngine):
    instance = NestedLevel1(next_=NestedLevel2(next_=NestedLevel3()))
    await aio_engine.save(instance)
    assert await aio_engine.count(NestedLevel3) == 1
    assert await aio_engine.count(NestedLevel2) == 1
    assert await aio_engine.count(NestedLevel1) == 1


def test_sync_save_deeply_nested(sync_engine: SyncEngine):
    instance = NestedLevel1(next_=NestedLevel2(next_=NestedLevel3()))
    sync_engine.save(instance)
    assert sync_engine.count(NestedLevel3) == 1
    assert sync_engine.count(NestedLevel2) == 1
    assert sync_engine.count(NestedLevel1) == 1


async def test_update_deeply_nested(aio_engine: AIOEngine):
    inst3 = NestedLevel3(
        field=0
    )  # Isolate inst3 to make sure it's not internaly copied
    instance = NestedLevel1(next_=NestedLevel2(next_=inst3))
    await aio_engine.save(instance)
    assert await aio_engine.count(NestedLevel3, NestedLevel3.field == 42) == 0
    inst3.field = 42
    await aio_engine.save(instance)
    assert await aio_engine.count(NestedLevel3, NestedLevel3.field == 42) == 1


def test_sync_update_deeply_nested(sync_engine: SyncEngine):
    inst3 = NestedLevel3(
        field=0
    )  # Isolate inst3 to make sure it's not internaly copied
    instance = NestedLevel1(next_=NestedLevel2(next_=inst3))
    sync_engine.save(instance)
    assert sync_engine.count(NestedLevel3, NestedLevel3.field == 42) == 0
    inst3.field = 42
    sync_engine.save(instance)
    assert sync_engine.count(NestedLevel3, NestedLevel3.field == 42) == 1


async def test_save_deeply_nested_and_fetch(aio_engine: AIOEngine):
    instance = NestedLevel1(next_=NestedLevel2(next_=NestedLevel3(field=0)))
    await aio_engine.save(instance)

    fetched = await aio_engine.find_one(NestedLevel1)
    assert fetched == instance


def test_sync_save_deeply_nested_and_fetch(sync_engine: SyncEngine):
    instance = NestedLevel1(next_=NestedLevel2(next_=NestedLevel3(field=0)))
    sync_engine.save(instance)

    fetched = sync_engine.find_one(NestedLevel1)
    assert fetched == instance


@only_on_replica
async def test_save_deeply_nested_and_fetch_with_transaction(aio_engine: AIOEngine):
    # Before MongoDB 4.4 it's necessary to create the collections before trying to use
    # them inside a transaction
    await aio_engine.database.create_collection(
        aio_engine.get_collection(NestedLevel1).name
    )
    await aio_engine.database.create_collection(
        aio_engine.get_collection(NestedLevel2).name
    )
    await aio_engine.database.create_collection(
        aio_engine.get_collection(NestedLevel3).name
    )

    instance = NestedLevel1(next_=NestedLevel2(next_=NestedLevel3(field=0)))
    async with await aio_engine.client.start_session() as session:
        async with session.start_transaction():
            await aio_engine.save(instance, session=session)

    fetched = await aio_engine.find_one(NestedLevel1)
    assert fetched == instance


@only_on_replica
def test_sync_save_deeply_nested_and_fetch_with_transaction(sync_engine: SyncEngine):
    # Before MongoDB 4.4 it's necessary to create the collections before trying to use
    # them inside a transaction
    sync_engine.database.create_collection(
        sync_engine.get_collection(NestedLevel1).name
    )
    sync_engine.database.create_collection(
        sync_engine.get_collection(NestedLevel2).name
    )
    sync_engine.database.create_collection(
        sync_engine.get_collection(NestedLevel3).name
    )

    instance = NestedLevel1(next_=NestedLevel2(next_=NestedLevel3(field=0)))
    with sync_engine.client.start_session() as session:
        with session.start_transaction():
            sync_engine.save(instance, session=session)

    fetched = sync_engine.find_one(NestedLevel1)
    assert fetched == instance


async def test_multiple_save_deeply_nested_and_fetch(aio_engine: AIOEngine):
    instances = [
        NestedLevel1(field=1, next_=NestedLevel2(field=2, next_=NestedLevel3(field=3))),
        NestedLevel1(field=4, next_=NestedLevel2(field=5, next_=NestedLevel3(field=6))),
    ]
    await aio_engine.save_all(instances)

    fetched = await aio_engine.find(NestedLevel1)
    assert len(fetched) == 2
    assert fetched[0] in instances
    assert fetched[1] in instances


@only_on_replica
async def test_multiple_save_deeply_nested_and_fetch_with_transaction(
    aio_engine: AIOEngine,
):
    # Before MongoDB 4.4 it's necessary to create the collections before trying to use
    # them inside a transaction
    await aio_engine.database.create_collection(
        aio_engine.get_collection(NestedLevel1).name
    )
    await aio_engine.database.create_collection(
        aio_engine.get_collection(NestedLevel2).name
    )
    await aio_engine.database.create_collection(
        aio_engine.get_collection(NestedLevel3).name
    )
    instances = [
        NestedLevel1(field=1, next_=NestedLevel2(field=2, next_=NestedLevel3(field=3))),
        NestedLevel1(field=4, next_=NestedLevel2(field=5, next_=NestedLevel3(field=6))),
    ]
    async with await aio_engine.client.start_session() as session:
        async with session.start_transaction():
            await aio_engine.save_all(instances, session=session)

    fetched = await aio_engine.find(NestedLevel1)
    assert len(fetched) == 2
    assert fetched[0] in instances
    assert fetched[1] in instances


@only_on_replica
def test_sync_multiple_save_deeply_nested_and_fetch_with_transaction(
    sync_engine: SyncEngine,
):
    # Before MongoDB 4.4 it's necessary to create the collections before trying to use
    # them inside a transaction
    sync_engine.database.create_collection(
        sync_engine.get_collection(NestedLevel1).name
    )
    sync_engine.database.create_collection(
        sync_engine.get_collection(NestedLevel2).name
    )
    sync_engine.database.create_collection(
        sync_engine.get_collection(NestedLevel3).name
    )
    instances = [
        NestedLevel1(field=1, next_=NestedLevel2(field=2, next_=NestedLevel3(field=3))),
        NestedLevel1(field=4, next_=NestedLevel2(field=5, next_=NestedLevel3(field=6))),
    ]
    with sync_engine.client.start_session() as session:
        with session.start_transaction():
            sync_engine.save_all(instances, session=session)

    fetched = list(sync_engine.find(NestedLevel1))
    assert len(fetched) == 2
    assert fetched[0] in instances
    assert fetched[1] in instances


def test_sync_multiple_save_deeply_nested_and_fetch(sync_engine: SyncEngine):
    instances = [
        NestedLevel1(field=1, next_=NestedLevel2(field=2, next_=NestedLevel3(field=3))),
        NestedLevel1(field=4, next_=NestedLevel2(field=5, next_=NestedLevel3(field=6))),
    ]
    sync_engine.save_all(instances)

    fetched = list(sync_engine.find(NestedLevel1))
    assert len(fetched) == 2
    assert fetched[0] in instances
    assert fetched[1] in instances


async def test_reference_with_key_name(aio_engine: AIOEngine):
    class R(Model):
        field: int

    class M(Model):
        r: R = Reference(key_name="fancy_key_name")

    instance = M(r=R(field=3))
    assert "fancy_key_name" in instance.model_dump_doc()
    await aio_engine.save(instance)

    fetched = await aio_engine.find_one(M)
    assert fetched is not None
    assert fetched.r.field == 3


def test_sync_reference_with_key_name(sync_engine: SyncEngine):
    class R(Model):
        field: int

    class M(Model):
        r: R = Reference(key_name="fancy_key_name")

    instance = M(r=R(field=3))
    assert "fancy_key_name" in instance.model_dump_doc()
    sync_engine.save(instance)

    fetched = sync_engine.find_one(M)
    assert fetched is not None
    assert fetched.r.field == 3


async def test_reference_not_set_in_database(aio_engine: AIOEngine):
    class R(Model):
        field: int

    class M(Model):
        r: R = Reference()

    oid = ObjectId()
    await aio_engine.get_collection(M).insert_one({"_id": oid})
    with pytest.raises(DocumentParsingError) as exc_info:
        await aio_engine.find_one(M)
    assert redact_objectid(str(exc_info.value), oid) == snapshot(
        """\
1 validation error for M
r
  Referenced document not found for foreign key 'r' [type=odmantic::referenced_document_not_found, input_value={'_id': ObjectId('<ObjectId>')}, input_type=dict]\
"""  # noqa: E501
    )


def test_sync_reference_not_set_in_database(sync_engine: SyncEngine):
    class R(Model):
        field: int

    class M(Model):
        r: R = Reference()

    oid = ObjectId()
    sync_engine.get_collection(M).insert_one({"_id": oid})
    with pytest.raises(DocumentParsingError) as exc_info:
        sync_engine.find_one(M)
    assert redact_objectid(str(exc_info.value), oid) == snapshot(
        """\
1 validation error for M
r
  Referenced document not found for foreign key 'r' [type=odmantic::referenced_document_not_found, input_value={'_id': ObjectId('<ObjectId>')}, input_type=dict]\
"""  # noqa: E501
    )


async def test_reference_incorect_reference_structure(aio_engine: AIOEngine):
    class R(Model):
        field: int

    class M(Model):
        r: R = Reference()

    r = R(field=12)
    r_doc = r.model_dump_doc()
    del r_doc["field"]
    m = M(r=r)
    await aio_engine.get_collection(R).insert_one(r_doc)
    await aio_engine.get_collection(M).insert_one(m.model_dump_doc())

    with pytest.raises(DocumentParsingError) as exc_info:
        await aio_engine.find_one(M)
    assert redact_objectid(str(exc_info.value), r.id) == snapshot(
        """\
1 validation error for M
r.field
  Key 'field' not found in document [type=odmantic::key_not_found_in_document, input_value={'_id': ObjectId('<ObjectId>')}, input_type=dict]\
"""  # noqa: E501
    )


def test_sync_reference_incorect_reference_structure(sync_engine: SyncEngine):
    class R(Model):
        field: int

    class M(Model):
        r: R = Reference()

    r = R(field=12)
    r_doc = r.model_dump_doc()
    del r_doc["field"]
    m = M(r=r)
    sync_engine.get_collection(R).insert_one(r_doc)
    sync_engine.get_collection(M).insert_one(m.model_dump_doc())

    with pytest.raises(DocumentParsingError) as exc_info:
        sync_engine.find_one(M)
    assert redact_objectid(str(exc_info.value), r.id) == snapshot(
        """\
1 validation error for M
r.field
  Key 'field' not found in document [type=odmantic::key_not_found_in_document, input_value={'_id': ObjectId('<ObjectId>')}, input_type=dict]\
"""  # noqa: E501
    )
