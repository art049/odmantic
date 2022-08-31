from datetime import datetime

import pytest

from odmantic.engine import AIOEngine, SyncEngine
from odmantic.model import Model
from odmantic.updater import currentDate
from tests.zoo.player import Player

from ..zoo.person import PersonModel
from ..zoo.pigment import Pigment
from ..zoo.student import Student

pytestmark = pytest.mark.asyncio


async def test_atomic_update_set(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        await session.save(PersonModel(first_name="John", last_name="Doe"))
        async with session.update(
            PersonModel, PersonModel.first_name == "John"
        ) as person:
            person.last_name = "Doe Doe"
        assert await session.count(PersonModel, PersonModel.last_name == "Doe Doe") == 1


def test_sync_atomic_update_set(sync_engine: SyncEngine):
    with sync_engine.session() as session:
        session.save(PersonModel(first_name="John", last_name="Doe"))
        with session.update(PersonModel, PersonModel.first_name == "John") as person:
            person.last_name = "Doe Doe"
        assert session.count(PersonModel, PersonModel.last_name == "Doe Doe") == 1


async def test_atomic_update_set_exited_context_value(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        await session.save(PersonModel(first_name="John", last_name="Doe"))
        # TODO: Can work with update one but for updating multiple models it might be
        #       complicated
        async with session.update(
            PersonModel, PersonModel.first_name == "John"
        ) as person:
            person.last_name = "Doe Doe"
        assert person.first_name == "John" and person.last_name == "Doe Doe"


def test_sync_atomic_update_set_exited_context_value(sync_engine: SyncEngine):
    with sync_engine.session() as session:
        session.save(PersonModel(first_name="John", last_name="Doe"))
        with session.update(PersonModel, PersonModel.first_name == "John") as person:
            person.last_name = "Doe Doe"
        assert person.first_name == "John" and person.last_name == "Doe Doe"


async def test_atomic_update_incr(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        await session.save(Player(name="Leeroy", level=1))
        async with session.update(Player, Player.name == "Leeroy") as player:
            player.level += 2
        assert await session.find_one(Player, Player.name == "Leeroy") == 3


def test_sync_atomic_update_incr(sync_engine: SyncEngine):
    with sync_engine.session() as session:
        session.save(Player(name="Leeroy", level=1))
        with session.update(Player, Player.name == "Leeroy") as player:
            player.level += 2
        assert session.find_one(Player, Player.name == "Leeroy") == 3


async def test_atomic_update_decr(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        await session.save(Player(name="Leeroy", level=10))
        async with session.update(Player, Player.name == "Leeroy") as player:
            player.level -= 5
        assert await session.find_one(Player, Player.name == "Leeroy") == 5


def test_sync_atomic_update_decr(sync_engine: SyncEngine):
    with sync_engine.session() as session:
        session.save(Player(name="Leeroy", level=10))
        with session.update(Player, Player.name == "Leeroy") as player:
            player.level -= 5
        assert session.find_one(Player, Player.name == "Leeroy") == 5


async def test_atomic_update_mul(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        await session.save(Player(name="Leeroy", level=2))
        async with session.update(Player, Player.name == "Leeroy") as player:
            player.level *= 5
        assert await session.find_one(Player, Player.name == "Leeroy") == 10


def test_sync_atomic_update_mul(sync_engine: SyncEngine):
    with sync_engine.session() as session:
        session.save(Player(name="Leeroy", level=2))
        with session.update(Player, Player.name == "Leeroy") as player:
            player.level *= 5
        assert session.find_one(Player, Player.name == "Leeroy") == 10


async def test_atomic_update_div_int(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        await session.save(Player(name="Leeroy", level=10))
        async with session.update(Player, Player.name == "Leeroy") as player:
            player.level //= 2
        assert await session.find_one(Player, Player.name == "Leeroy") == 5


def test_sync_atomic_update_div_int(sync_engine: SyncEngine):
    with sync_engine.session() as session:
        session.save(Player(name="Leeroy", level=10))
        with session.update(Player, Player.name == "Leeroy") as player:
            player.level //= 2
        assert session.find_one(Player, Player.name == "Leeroy") == 5


class ModelWithDate(Model):
    updated_at: datetime


async def test_atomic_update_current_datetime(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        await session.save(ModelWithDate(updated_at=datetime(0, 0, 0)))
        async with session.update(ModelWithDate) as m:
            m.updated_at = currentDate()
        fetched = await session.find_one(ModelWithDate)
        assert fetched is not None
        assert fetched.updated_at > datetime(0, 0, 0)


def test_sync_atomic_update_current_datetime(sync_engine: SyncEngine):
    with sync_engine.session() as session:
        session.save(ModelWithDate(updated_at=datetime(0, 0, 0)))
        with session.update(ModelWithDate) as m:
            m.updated_at = currentDate()
        fetched = session.find_one(ModelWithDate)
        assert fetched is not None
        assert fetched.updated_at > datetime(0, 0, 0)


async def test_atomic_update_array_push_append_extend(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        await session.save(Student(scores=[70, 85]))
        async with session.update(Student) as student:
            student.scores.append(100)
        async with session.update(Student) as student:
            student.scores.extend([95, 100])
        fetched = await session.find_one(Student)
        assert fetched is not None and fetched.scores == [70, 85, 90, 95, 100]


def test_sync_atomic_update_array_push_append_extend(sync_engine: SyncEngine):
    with sync_engine.session() as session:
        session.save(Student(scores=[70, 85]))
        with session.update(Student) as student:
            student.scores.append(90)
        with session.update(Student) as student:
            student.scores.extend([95, 100])
        fetched = session.find_one(Student)
        assert fetched is not None and fetched.scores == [70, 85, 90, 95, 100]


async def test_atomic_update_array_add_to_set(aio_engine: AIOEngine):
    async with aio_engine.session() as session:
        await session.save(Pigment(colors={"cyan", "red"}))
        async with session.update(Pigment) as pigment:
            pigment.colors.add("yellow")
        fetched = await session.find_one(Pigment)
        assert fetched is not None and fetched.colors == {"cyan", "red", "yellow"}


def test_sync_atomic_update_array_add_to_set(sync_engine: SyncEngine):
    with sync_engine.session() as session:
        session.save(Pigment(colors={"cyan", "red"}))
        with session.update(Pigment) as pigment:
            pigment.colors.add("yellow")
        fetched = session.find_one(Pigment)
        assert fetched is not None and fetched.colors == {"cyan", "red", "yellow"}
