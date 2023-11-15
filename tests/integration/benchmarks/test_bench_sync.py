import pytest

from odmantic import SyncEngine

from .models import VALID_LEVELS, SmallJournal


@pytest.fixture(params=[10, 50, 100])
def count(request):
    return request.param


def test_insert_small_single(benchmark, sync_engine: SyncEngine, count: int):
    instances = list(SmallJournal.get_random_instances("test_write_small", count))

    @benchmark
    def _():
        for instance in instances:
            sync_engine.save(instance)


def test_write_small_bulk(
    benchmark,
    sync_engine: SyncEngine,
    count: int,
):
    instances = list(SmallJournal.get_random_instances("test_write_small", count))

    @benchmark
    def _():
        sync_engine.save_all(instances)


def test_filter_by_level_small(benchmark, sync_engine: SyncEngine, count: int):
    instances = list(SmallJournal.get_random_instances("test_write_small", count))
    sync_engine.save_all(instances)

    @benchmark
    def _():
        total = 0
        for level in VALID_LEVELS:
            total += len(
                list(sync_engine.find(SmallJournal, SmallJournal.level == level))
            )


def test_filter_limit_skip_by_level_small(
    benchmark, sync_engine: SyncEngine, count: int
):
    instances = list(SmallJournal.get_random_instances("test_write_small", count))
    sync_engine.save_all(instances)

    @benchmark
    def _():
        total = 0
        for level in VALID_LEVELS:
            total += len(
                list(
                    sync_engine.find(
                        SmallJournal, SmallJournal.level == level, limit=20, skip=20
                    )
                )
            )


def test_find_one_by_id(benchmark, sync_engine: SyncEngine, count: int):
    instances = list(SmallJournal.get_random_instances("test_write_small", count))
    sync_engine.save_all(instances)
    ids = [instance.id for instance in instances]

    @benchmark
    def _():
        for id_ in ids:
            sync_engine.find_one(SmallJournal, SmallJournal.id == id_)
