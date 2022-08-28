import pytest

from odmantic.engine import AIOEngine, SyncEngine
from odmantic.session import AIOTransaction, SyncTransaction
from tests.integration.conftest import only_on_replica

from ..zoo.person import PersonModel

pytestmark = pytest.mark.asyncio


class CustomException(Exception):
    pass


async def test_session_exception_propagation(aio_engine: AIOEngine):
    with pytest.raises(CustomException):
        async with aio_engine.session():
            raise CustomException()


def test_sync_session_exception_propagation(sync_engine: SyncEngine):
    with pytest.raises(CustomException):
        with sync_engine.session():
            raise CustomException()


@only_on_replica
async def test_transaction_exception_propagation(aio_engine: AIOEngine):
    with pytest.raises(CustomException):
        async with aio_engine.transaction():
            raise CustomException()


@only_on_replica
def test_sync_transaction_exception_propagation(sync_engine: SyncEngine):
    with pytest.raises(CustomException):
        with sync_engine.session():
            raise CustomException()


async def test_start_session_twice(aio_engine: AIOEngine):
    with pytest.raises(RuntimeError, match="Session is already started"):
        async with aio_engine.session() as session:
            await session.start()


def test_sync_start_session_twice(sync_engine: SyncEngine):
    with pytest.raises(RuntimeError, match="Session is already started"):
        with sync_engine.session() as session:
            session.start()


async def test_end_a_non_started_session(aio_engine: AIOEngine):
    with pytest.raises(RuntimeError, match="Session is not started"):
        await aio_engine.session().end()


def test_sync_end_a_non_started_session(sync_engine: SyncEngine):
    with pytest.raises(RuntimeError, match="Session is not started"):
        sync_engine.session().end()


@only_on_replica
async def test_start_transaction_twice(aio_engine: AIOEngine):
    with pytest.raises(RuntimeError, match="Transaction already started"):
        async with aio_engine.transaction() as transaction:
            await transaction.start()


@only_on_replica
def test_sync_start_transaction_twice(sync_engine: SyncEngine):
    with pytest.raises(RuntimeError, match="Transaction already started"):
        with sync_engine.transaction() as transaction:
            transaction.start()


@only_on_replica
async def test_abort_a_non_started_transaction(aio_engine: AIOEngine):
    with pytest.raises(RuntimeError, match="Transaction not started"):
        await aio_engine.transaction().abort()


@only_on_replica
def test_sync_abort_a_non_started_transaction(sync_engine: SyncEngine):
    with pytest.raises(RuntimeError, match="Transaction not started"):
        sync_engine.transaction().abort()


@only_on_replica
async def test_commit_a_non_started_transaction(aio_engine: AIOEngine):
    with pytest.raises(RuntimeError, match="Transaction not started"):
        await aio_engine.transaction().commit()


@only_on_replica
def test_sync_commit_a_non_started_transaction(sync_engine: SyncEngine):
    with pytest.raises(RuntimeError, match="Transaction not started"):
        sync_engine.transaction().commit()


@only_on_replica
async def test_create_transaction_with_a_non_started_session(aio_engine: AIOEngine):
    with pytest.raises(RuntimeError, match="provided session is not started"):
        session = aio_engine.session()
        AIOTransaction(session)


@only_on_replica
async def test_sync_create_transaction_with_a_non_started_session(
    sync_engine: SyncEngine,
):
    with pytest.raises(RuntimeError, match="provided session is not started"):
        session = sync_engine.session()
        SyncTransaction(session)


async def test_operation_on_ended_session_should_fail(aio_engine: AIOEngine):
    session = aio_engine.session()
    await session.start()
    await session.end()
    with pytest.raises(RuntimeError, match="session not started"):
        await session.save(PersonModel(first_name="Jean-Pierre", last_name="Pernaud"))


def test_sync_operation_on_ended_session_should_fail(sync_engine: SyncEngine):
    session = sync_engine.session()
    session.start()
    session.end()
    with pytest.raises(RuntimeError, match="session not started"):
        session.save(PersonModel(first_name="Jean-Pierre", last_name="Pernaud"))


@only_on_replica
async def test_operation_on_aborted_transaction_should_fail(aio_engine: AIOEngine):
    transaction = aio_engine.transaction()
    await transaction.start()
    await transaction.abort()
    with pytest.raises(RuntimeError, match="transaction not started"):
        await transaction.save(
            PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
        )


@only_on_replica
def test_sync_operation_on_aborted_transaction_should_fail(sync_engine: SyncEngine):
    transaction = sync_engine.transaction()
    transaction.start()
    transaction.abort()
    with pytest.raises(RuntimeError, match="transaction not started"):
        transaction.save(PersonModel(first_name="Jean-Pierre", last_name="Pernaud"))


@only_on_replica
async def test_operation_on_comitted_transaction_should_fail(aio_engine: AIOEngine):
    transaction = aio_engine.transaction()
    await transaction.start()
    await transaction.commit()
    with pytest.raises(RuntimeError, match="transaction not started"):
        await transaction.save(
            PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
        )


@only_on_replica
def test_sync_operation_on_comitted_transaction_should_fail(sync_engine: SyncEngine):
    transaction = sync_engine.transaction()
    transaction.start()
    transaction.commit()
    with pytest.raises(RuntimeError, match="transaction not started"):
        transaction.save(PersonModel(first_name="Jean-Pierre", last_name="Pernaud"))


async def test_operation_on_exited_context_session_sould_fail(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        pass
    with pytest.raises(RuntimeError, match="session not started"):
        await session.save(PersonModel(first_name="Jean-Pierre", last_name="Pernaud"))


async def test_sync_operation_on_exited_context_session_sould_fail(
    sync_engine: SyncEngine,
):
    with sync_engine.session() as session:
        pass
    with pytest.raises(RuntimeError, match="session not started"):
        session.save(PersonModel(first_name="Jean-Pierre", last_name="Pernaud"))


@only_on_replica
async def test_operation_on_exited_context_transaction_sould_fail(
    aio_engine: AIOEngine,
):
    async with aio_engine.transaction() as transaction:
        pass
    with pytest.raises(RuntimeError, match="transaction not started"):
        await transaction.save(
            PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
        )


@only_on_replica
async def test_sync_operation_on_exited_context_transaction_sould_fail(
    sync_engine: SyncEngine,
):
    with sync_engine.transaction() as transaction:
        pass
    with pytest.raises(RuntimeError, match="transaction not started"):
        transaction.save(PersonModel(first_name="Jean-Pierre", last_name="Pernaud"))


@only_on_replica
async def test_operation_on_exited_context_aborted_transaction_sould_fail(
    aio_engine: AIOEngine,
):
    async with aio_engine.transaction() as transaction:
        await transaction.abort()
    with pytest.raises(RuntimeError, match="transaction not started"):
        await transaction.find_one(PersonModel, PersonModel.first_name == "Jean-Pierre")


@only_on_replica
def test_sync_operation_on_exited_context_aborted_transaction_sould_fail(
    sync_engine: SyncEngine,
):
    with sync_engine.transaction() as transaction:
        transaction.abort()
    with pytest.raises(RuntimeError, match="transaction not started"):
        transaction.find_one(PersonModel, PersonModel.first_name == "Jean-Pierre")


@only_on_replica
async def test_session_stopped_on_manual_transaction_commit(
    aio_engine: AIOEngine,
):
    transaction = aio_engine.transaction()
    await transaction.start()
    await transaction.commit()
    assert not transaction.session.is_started


@only_on_replica
def test_sync_session_stopped_on_manual_transaction_commit(
    sync_engine: SyncEngine,
):
    transaction = sync_engine.transaction()
    transaction.start()
    transaction.commit()
    assert not transaction.session.is_started


@only_on_replica
async def test_session_stopped_on_manual_transaction_abort(
    aio_engine: AIOEngine,
):
    transaction = aio_engine.transaction()
    await transaction.start()
    await transaction.abort()
    assert not transaction.session.is_started


@only_on_replica
def test_sync_session_stopped_on_manual_transaction_abort(
    sync_engine: SyncEngine,
):
    transaction = sync_engine.transaction()
    transaction.start()
    transaction.abort()
    assert not transaction.session.is_started


@only_on_replica
async def test_abort_transaction_keep_provided_session_opened(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        async with session.transaction() as transaction:
            await transaction.abort()
        assert session.is_started


@only_on_replica
def test_sync_abort_transaction_keep_provided_session_opened(sync_engine: SyncEngine):
    with sync_engine.session() as session:
        with session.transaction() as transaction:
            transaction.abort()
        assert session.is_started


async def test_save_find_find_one_session(aio_engine: AIOEngine):
    initial_instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    async with aio_engine.session() as session:
        await session.save(initial_instance)
        found_instances = await session.find(PersonModel)
        assert len(found_instances) == 1
        assert found_instances[0].first_name == initial_instance.first_name
        assert found_instances[0].last_name == initial_instance.last_name

        single_fetched_instance = await session.find_one(
            PersonModel, PersonModel.first_name == "Jean-Pierre"
        )
        assert single_fetched_instance is not None
        assert single_fetched_instance.first_name == initial_instance.first_name
        assert single_fetched_instance.last_name == initial_instance.last_name


def test_sync_save_find_find_one_session(sync_engine: SyncEngine):
    initial_instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    with sync_engine.session() as session:
        session.save(initial_instance)
        found_instances = list(session.find(PersonModel))
        assert len(found_instances) == 1
        assert found_instances[0].first_name == initial_instance.first_name
        assert found_instances[0].last_name == initial_instance.last_name

        single_fetched_instance = session.find_one(
            PersonModel, PersonModel.first_name == "Jean-Pierre"
        )
        assert single_fetched_instance is not None
        assert single_fetched_instance.first_name == initial_instance.first_name
        assert single_fetched_instance.last_name == initial_instance.last_name


@only_on_replica
async def test_save_find_find_one_session_transaction(aio_engine: AIOEngine):
    initial_instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    async with aio_engine.session() as session:
        async with session.transaction() as tx:
            await tx.save(initial_instance)
            found_instances = await tx.find(PersonModel)
            assert len(found_instances) == 1
            assert found_instances[0].first_name == initial_instance.first_name
            assert found_instances[0].last_name == initial_instance.last_name

            single_fetched_instance = await tx.find_one(
                PersonModel, PersonModel.first_name == "Jean-Pierre"
            )
            assert single_fetched_instance is not None
            assert single_fetched_instance.first_name == initial_instance.first_name
            assert single_fetched_instance.last_name == initial_instance.last_name
            await tx.commit()


@only_on_replica
def test_sync_save_find_find_one_session_transaction(sync_engine: SyncEngine):
    initial_instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    with sync_engine.session() as session:
        with session.transaction() as tx:
            tx.save(initial_instance)
            found_instances = list(tx.find(PersonModel))
            assert len(found_instances) == 1
            assert found_instances[0].first_name == initial_instance.first_name
            assert found_instances[0].last_name == initial_instance.last_name

            single_fetched_instance = tx.find_one(
                PersonModel, PersonModel.first_name == "Jean-Pierre"
            )
            assert single_fetched_instance is not None
            assert single_fetched_instance.first_name == initial_instance.first_name
            assert single_fetched_instance.last_name == initial_instance.last_name
            tx.commit()


@only_on_replica
async def test_save_transaction_abort(aio_engine: AIOEngine):
    initial_instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    async with aio_engine.transaction() as tx:
        await tx.save(initial_instance)
        found_instances = await tx.find(PersonModel)
        assert len(found_instances) == 1
        assert found_instances[0].first_name == initial_instance.first_name
        assert found_instances[0].last_name == initial_instance.last_name
        await tx.abort()

    single_fetched_instance = await aio_engine.find_one(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )
    assert single_fetched_instance is None


@only_on_replica
def test_sync_save_transaction_abort(sync_engine: SyncEngine):
    initial_instance = PersonModel(first_name="Jean-Pierre", last_name="Pernaud")
    with sync_engine.transaction() as tx:
        tx.save(initial_instance)
        found_instances = list(tx.find(PersonModel))
        assert len(found_instances) == 1
        assert found_instances[0].first_name == initial_instance.first_name
        assert found_instances[0].last_name == initial_instance.last_name
        tx.abort()
    single_fetched_instance = sync_engine.find_one(
        PersonModel, PersonModel.first_name == "Jean-Pierre"
    )
    assert single_fetched_instance is None
