import pymongo
import pytest

from odmantic.engine import AIOEngine, SyncEngine
from odmantic.exceptions import DuplicateKeyError
from odmantic.field import Field
from odmantic.index import Index
from odmantic.model import Model
from odmantic.query import asc, desc

pytestmark = pytest.mark.asyncio


async def test_single_field_index_creation(aio_engine: AIOEngine):
    class M(Model):
        f: int = Field(index=True)

    await aio_engine.configure_database([M])

    info = await aio_engine.get_collection(M).index_information()
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1)], info.values()),
            None,
        )
        is not None
    )


def test_sync_single_field_index_creation(sync_engine: SyncEngine):
    class M(Model):
        f: int = Field(index=True)

    sync_engine.configure_database([M])

    info = sync_engine.get_collection(M).index_information()
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1)], info.values()),
            None,
        )
        is not None
    )


async def test_single_field_index_creation_unique(aio_engine: AIOEngine):
    class M(Model):
        f: int = Field(unique=True)

    await aio_engine.configure_database([M])

    info = await aio_engine.get_collection(M).index_information()
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1)] and v["unique"], info.values()),
            None,
        )
        is not None
    )


def test_sync_single_field_index_creation_unique(sync_engine: SyncEngine):
    class M(Model):
        f: int = Field(unique=True)

    sync_engine.configure_database([M])

    info = sync_engine.get_collection(M).index_information()
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1)] and v["unique"], info.values()),
            None,
        )
        is not None
    )


async def test_compound_index_with_name(aio_engine: AIOEngine):
    class M(Model):
        f: int
        g: int

        class Config:
            @staticmethod
            def indexes():
                yield Index(asc(M.f), desc(M.g), name="test")

    await aio_engine.configure_database([M])

    info = await aio_engine.get_collection(M).index_information()
    assert "test" in info
    assert info["test"]["key"] == [("f", 1), ("g", -1)]


def test_sync_compound_index_with_name(sync_engine: SyncEngine):
    class M(Model):
        f: int
        g: int

        class Config:
            @staticmethod
            def indexes():
                yield Index(asc(M.f), desc(M.g), name="test")

    sync_engine.configure_database([M])

    info = sync_engine.get_collection(M).index_information()
    assert "test" in info
    assert info["test"]["key"] == [("f", 1), ("g", -1)]


async def test_multiple_indexes(aio_engine: AIOEngine):
    class M(Model):
        f: int
        g: int = Field(unique=True)

        class Config:
            @staticmethod
            def indexes():
                yield Index(asc(M.f))
                yield Index(asc(M.f), desc(M.g))

    await aio_engine.configure_database([M])

    info = await aio_engine.get_collection(M).index_information()
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1)], info.values()),
            None,
        )
        is not None
    )
    assert (
        next(
            filter(lambda v: v["key"] == [("g", 1)] and v["unique"], info.values()),
            None,
        )
        is not None
    )
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1), ("g", -1)], info.values()),
            None,
        )
        is not None
    )


def test_sync_multiple_indexes(sync_engine: SyncEngine):
    class M(Model):
        f: int
        g: int = Field(unique=True)

        class Config:
            @staticmethod
            def indexes():
                yield Index(asc(M.f))
                yield Index(asc(M.f), desc(M.g))

    sync_engine.configure_database([M])

    info = sync_engine.get_collection(M).index_information()
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1)], info.values()),
            None,
        )
        is not None
    )
    assert (
        next(
            filter(lambda v: v["key"] == [("g", 1)] and v["unique"], info.values()),
            None,
        )
        is not None
    )
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1), ("g", -1)], info.values()),
            None,
        )
        is not None
    )


async def test_unique_index_duplicate_save(aio_engine: AIOEngine):
    class M(Model):
        f: int = Field(unique=True)

    await aio_engine.configure_database([M])

    await aio_engine.save(M(f=1))
    duplicated_instance = M(f=1)
    with pytest.raises(DuplicateKeyError) as e:
        await aio_engine.save(duplicated_instance)
    assert e.value.instance == duplicated_instance


def test_sync_unique_index_duplicate_save(sync_engine: SyncEngine):
    class M(Model):
        f: int = Field(unique=True)

    sync_engine.configure_database([M])

    sync_engine.save(M(f=1))
    duplicated_instance = M(f=1)
    with pytest.raises(DuplicateKeyError) as e:
        sync_engine.save(duplicated_instance)
    assert e.value.instance == duplicated_instance


async def test_double_index_creation(aio_engine: AIOEngine):
    class M(Model):
        f: int = Field(index=True)

    await aio_engine.configure_database([M])
    await aio_engine.configure_database([M])

    info = await aio_engine.get_collection(M).index_information()
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1)], info.values()),
            None,
        )
        is not None
    )


def test_sync_double_index_creation(sync_engine: SyncEngine):
    class M(Model):
        f: int = Field(index=True)

    sync_engine.configure_database([M])
    sync_engine.configure_database([M])

    info = sync_engine.get_collection(M).index_information()
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1)], info.values()),
            None,
        )
        is not None
    )


async def test_index_update_failure(aio_engine: AIOEngine):
    class M(Model):
        f: int = Field(unique=True)

        class Config:
            collection = "test"

    await aio_engine.configure_database([M])

    class M2(Model):
        f: int = Field(index=True)

        class Config:
            collection = "test"

    with pytest.raises(pymongo.errors.OperationFailure):
        await aio_engine.configure_database([M2])


def test_sync_index_update_failure(sync_engine: SyncEngine):
    class M(Model):
        f: int = Field(unique=True)

        class Config:
            collection = "test"

    sync_engine.configure_database([M])

    class M2(Model):
        f: int = Field(index=True)

        class Config:
            collection = "test"

    with pytest.raises(pymongo.errors.OperationFailure):
        sync_engine.configure_database([M2])


async def test_index_replacement(aio_engine: AIOEngine):
    class M(Model):
        f: int = Field(unique=True)

        class Config:
            collection = "test"

    await aio_engine.configure_database([M])
    info = await aio_engine.get_collection(M).index_information()
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1)] and v["unique"], info.values()),
            None,
        )
        is not None
    )

    class M2(Model):
        f: int = Field(index=True)

        class Config:
            collection = "test"

    await aio_engine.configure_database([M2], update_existing_indexes=True)
    info = await aio_engine.get_collection(M).index_information()
    assert (
        next(
            filter(
                lambda v: v["key"] == [("f", 1)] and "unique" not in v, info.values()
            ),
            None,
        )
        is not None
    )


def test_sync_index_replacement(sync_engine: SyncEngine):
    class M(Model):
        f: int = Field(unique=True)

        class Config:
            collection = "test"

    sync_engine.configure_database([M])
    info = sync_engine.get_collection(M).index_information()
    assert (
        next(
            filter(lambda v: v["key"] == [("f", 1)] and v["unique"], info.values()),
            None,
        )
        is not None
    )

    class M2(Model):
        f: int = Field(index=True)

        class Config:
            collection = "test"

    sync_engine.configure_database([M2], update_existing_indexes=True)
    info = sync_engine.get_collection(M).index_information()
    assert (
        next(
            filter(
                lambda v: v["key"] == [("f", 1)] and "unique" not in v, info.values()
            ),
            None,
        )
        is not None
    )


async def test_custom_text_index(aio_engine: AIOEngine):
    class Post(Model):
        title: str
        content: str

        class Config:
            @staticmethod
            def indexes():
                yield pymongo.IndexModel(
                    [("title", pymongo.TEXT), ("content", pymongo.TEXT)]
                )

    await aio_engine.configure_database([Post])
    await aio_engine.save(Post(title="My post on python", content="It's awesome!"))
    assert await aio_engine.find_one(Post, {"$text": {"$search": "python"}}) is not None


async def test_sync_custom_text_index(sync_engine: SyncEngine):
    class Post(Model):
        title: str
        content: str

        class Config:
            @staticmethod
            def indexes():
                yield pymongo.IndexModel(
                    [("title", pymongo.TEXT), ("content", pymongo.TEXT)]
                )

    sync_engine.configure_database([Post])
    sync_engine.save(Post(title="My post on python", content="It's awesome!"))
    assert sync_engine.find_one(Post, {"$text": {"$search": "python"}}) is not None
