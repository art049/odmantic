import sys
from unittest.mock import MagicMock, Mock

import pytest

from odmantic.session import AIOSession, AIOTransaction, SyncSession, SyncTransaction

from ..zoo.person import PersonModel

if sys.version_info >= (3, 8):
    from unittest.mock import AsyncMock


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        sys.version_info < (3, 8), reason="async mock testing requires python3.8+"
    ),
]


@pytest.fixture(scope="function")
def mocked_driver_session():
    return Mock()


@pytest.fixture(scope="function")
def mocked_aio_engine(mocked_driver_session):
    engine = AsyncMock()
    engine._get_session = Mock(return_value=mocked_driver_session)
    return engine


@pytest.fixture(scope="function", params=["session", "transaction"])
async def mocked_aio_session(request, mocked_aio_engine):
    if request.param == "session":
        return AIOSession(mocked_aio_engine)
    else:
        session = AIOSession(mocked_aio_engine)
        await session.start()
        return AIOTransaction(session)


@pytest.fixture(scope="function")
def mocked_sync_engine(mocked_driver_session):
    engine = MagicMock()
    engine._get_session = Mock(return_value=mocked_driver_session)
    return engine


@pytest.fixture(scope="function", params=["session", "transaction"])
def mocked_sync_session(request, mocked_sync_engine):
    if request.param == "session":
        return SyncSession(mocked_sync_engine)
    else:
        session = SyncSession(mocked_sync_engine)
        session.start()
        return SyncTransaction(session)


async def test_session_find(
    mocked_aio_session, mocked_aio_engine, mocked_driver_session
):
    await mocked_aio_session.find(PersonModel)
    mocked_aio_engine.find.assert_awaited_once()
    assert mocked_aio_engine.find.call_args.kwargs["session"] == mocked_driver_session


async def test_session_find_one(
    mocked_aio_session, mocked_aio_engine, mocked_driver_session
):
    await mocked_aio_session.find_one(PersonModel)
    mocked_aio_engine.find_one.assert_awaited_once()
    assert (
        mocked_aio_engine.find_one.call_args.kwargs["session"] == mocked_driver_session
    )


async def test_session_count(
    mocked_aio_session, mocked_aio_engine, mocked_driver_session
):
    await mocked_aio_session.count(PersonModel)
    mocked_aio_engine.count.assert_awaited_once()
    assert mocked_aio_engine.count.call_args.kwargs["session"] == mocked_driver_session


async def test_session_save(
    mocked_aio_session, mocked_aio_engine, mocked_driver_session
):
    await mocked_aio_session.save(PersonModel(first_name="John", last_name="Doe"))
    mocked_aio_engine.save.assert_awaited_once()
    assert mocked_aio_engine.save.call_args.kwargs["session"] == mocked_driver_session


async def test_session_save_all(
    mocked_aio_session, mocked_aio_engine, mocked_driver_session
):
    await mocked_aio_session.save_all([PersonModel(first_name="John", last_name="Doe")])
    mocked_aio_engine.save_all.assert_awaited_once()
    assert (
        mocked_aio_engine.save_all.call_args.kwargs["session"] == mocked_driver_session
    )


async def test_session_delete(
    mocked_aio_session, mocked_aio_engine, mocked_driver_session
):
    await mocked_aio_session.delete(PersonModel(first_name="John", last_name="Doe"))
    mocked_aio_engine.delete.assert_awaited_once()
    assert mocked_aio_engine.delete.call_args.kwargs["session"] == mocked_driver_session


async def test_session_remove(
    mocked_aio_session, mocked_aio_engine, mocked_driver_session
):
    await mocked_aio_session.remove(PersonModel, PersonModel.first_name == "John")
    mocked_aio_engine.remove.assert_awaited_once()
    assert mocked_aio_engine.remove.call_args.kwargs["session"] == mocked_driver_session


def test_sync_session_find(
    mocked_sync_session, mocked_sync_engine, mocked_driver_session
):
    mocked_sync_session.find(PersonModel)
    mocked_sync_engine.find.assert_called_once()
    assert mocked_sync_engine.find.call_args.kwargs["session"] == mocked_driver_session


def test_sync_session_find_one(
    mocked_sync_session, mocked_sync_engine, mocked_driver_session
):
    mocked_sync_session.find_one(PersonModel)
    mocked_sync_engine.find_one.assert_called_once()
    assert (
        mocked_sync_engine.find_one.call_args.kwargs["session"] == mocked_driver_session
    )


def test_sync_session_count(
    mocked_sync_session, mocked_sync_engine, mocked_driver_session
):
    mocked_sync_session.count(PersonModel)
    mocked_sync_engine.count.assert_called_once()
    assert mocked_sync_engine.count.call_args.kwargs["session"] == mocked_driver_session


def test_sync_session_save(
    mocked_sync_session, mocked_sync_engine, mocked_driver_session
):
    mocked_sync_session.save(PersonModel(first_name="John", last_name="Doe"))
    mocked_sync_engine.save.assert_called_once()
    assert mocked_sync_engine.save.call_args.kwargs["session"] == mocked_driver_session


def test_sync_session_save_all(
    mocked_sync_session, mocked_sync_engine, mocked_driver_session
):
    mocked_sync_session.save_all([PersonModel(first_name="John", last_name="Doe")])
    mocked_sync_engine.save_all.assert_called_once()
    assert (
        mocked_sync_engine.save_all.call_args.kwargs["session"] == mocked_driver_session
    )


def test_sync_session_delete(
    mocked_sync_session, mocked_sync_engine, mocked_driver_session
):
    mocked_sync_session.delete(PersonModel(first_name="John", last_name="Doe"))
    mocked_sync_engine.delete.assert_called_once()
    assert (
        mocked_sync_engine.delete.call_args.kwargs["session"] == mocked_driver_session
    )


def test_sync_session_remove(
    mocked_sync_session, mocked_sync_engine, mocked_driver_session
):
    mocked_sync_session.remove(PersonModel, PersonModel.first_name == "John")
    mocked_sync_engine.remove.assert_called_once()
    assert (
        mocked_sync_engine.remove.call_args.kwargs["session"] == mocked_driver_session
    )
