import pytest

from odmantic import AIOEngine

from .models import VALID_LEVELS, SmallJournal

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skip("@benchmark does not support async functions yet"),
]


@pytest.fixture(params=[10, 50, 100])
def count(request):
    return request.param


async def test_insert_small_single(benchmark, aio_engine: AIOEngine, count: int):
    instances = list(SmallJournal.get_random_instances("test_write_small", count))

    @benchmark
    async def _():
        for instance in instances:
            await aio_engine.save(instance)


async def test_write_small_bulk(
    benchmark,
    aio_engine: AIOEngine,
    count: int,
):
    instances = list(SmallJournal.get_random_instances("test_write_small", count))

    @benchmark
    async def _():
        await aio_engine.save_all(instances)


async def test_filter_by_level_small(benchmark, aio_engine: AIOEngine, count: int):
    instances = list(SmallJournal.get_random_instances("test_write_small", count))
    await aio_engine.save_all(instances)

    @benchmark
    async def _():
        total = 0
        for level in VALID_LEVELS:
            total += len(
                await aio_engine.find(SmallJournal, SmallJournal.level == level)
            )


async def test_filter_limit_skip_by_level_small(
    benchmark, aio_engine: AIOEngine, count: int
):
    instances = list(SmallJournal.get_random_instances("test_write_small", count))
    await aio_engine.save_all(instances)

    @benchmark
    async def _():
        total = 0
        for level in VALID_LEVELS:
            total += len(
                await aio_engine.find(
                    SmallJournal, SmallJournal.level == level, limit=20, skip=20
                )
            )


async def test_find_one_by_id(benchmark, aio_engine: AIOEngine, count: int):
    instances = list(SmallJournal.get_random_instances("test_write_small", count))
    await aio_engine.save_all(instances)
    ids = [instance.id for instance in instances]

    @benchmark
    async def _():
        for id_ in ids:
            await aio_engine.find_one(SmallJournal, SmallJournal.id == id_)
