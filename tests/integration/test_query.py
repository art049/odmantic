import re
from typing import cast

import pytest

from odmantic import Model
from odmantic.engine import AIOEngine, SyncEngine
from odmantic.query import (
    QueryExpression,
    and_,
    eq,
    gt,
    gte,
    in_,
    lt,
    lte,
    match,
    ne,
    nor_,
    not_in,
    or_,
)

from ..zoo.person import PersonModel

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="function")
async def person_persisted(aio_engine: AIOEngine):
    initial_instances = [
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud"),
        PersonModel(first_name="Jean-Pierre", last_name="Castaldi"),
        PersonModel(first_name="Michel", last_name="Drucker"),
    ]
    return await aio_engine.save_all(initial_instances)


@pytest.mark.usefixtures("person_persisted")
async def test_and(aio_engine: AIOEngine):
    query = (PersonModel.first_name == "Michel") & (PersonModel.last_name == "Drucker")
    assert query == and_(
        PersonModel.first_name == "Michel", PersonModel.last_name == "Drucker"
    )
    count = await aio_engine.count(PersonModel, query)
    assert count == 1


@pytest.mark.usefixtures("person_persisted")
def test_sync_and(sync_engine: SyncEngine):
    query = (PersonModel.first_name == "Michel") & (PersonModel.last_name == "Drucker")
    assert query == and_(
        PersonModel.first_name == "Michel", PersonModel.last_name == "Drucker"
    )
    count = sync_engine.count(PersonModel, query)
    assert count == 1


@pytest.mark.usefixtures("person_persisted")
async def test_or(aio_engine: AIOEngine):
    query = (PersonModel.first_name == "Michel") | (PersonModel.last_name == "Castaldi")
    assert query == or_(
        PersonModel.first_name == "Michel", PersonModel.last_name == "Castaldi"
    )
    count = await aio_engine.count(PersonModel, query)
    assert count == 2


@pytest.mark.usefixtures("person_persisted")
def test_sync_or(sync_engine: SyncEngine):
    query = (PersonModel.first_name == "Michel") | (PersonModel.last_name == "Castaldi")
    assert query == or_(
        PersonModel.first_name == "Michel", PersonModel.last_name == "Castaldi"
    )
    count = sync_engine.count(PersonModel, query)
    assert count == 2


@pytest.mark.usefixtures("person_persisted")
async def test_nor(aio_engine: AIOEngine):
    count = await aio_engine.count(
        PersonModel,
        nor_(PersonModel.first_name == "Michel", PersonModel.last_name == "Castaldi"),
    )
    assert count == 1


@pytest.mark.usefixtures("person_persisted")
async def test_eq(aio_engine: AIOEngine):
    query = cast(QueryExpression, PersonModel.first_name == "Michel")
    assert query == eq(PersonModel.first_name, "Michel")
    count = await aio_engine.count(PersonModel, query)
    assert count == 1


@pytest.mark.usefixtures("person_persisted")
def test_sync_eq(sync_engine: SyncEngine):
    query = cast(QueryExpression, PersonModel.first_name == "Michel")
    assert query == eq(PersonModel.first_name, "Michel")
    count = sync_engine.count(PersonModel, query)
    assert count == 1


@pytest.mark.usefixtures("person_persisted")
async def test_ne(aio_engine: AIOEngine):
    query = PersonModel.first_name != "Michel"
    assert query == ne(PersonModel.first_name, "Michel")
    count = await aio_engine.count(PersonModel, query)
    assert count == 2


@pytest.mark.usefixtures("person_persisted")
def test_sync_ne(sync_engine: SyncEngine):
    query = PersonModel.first_name != "Michel"
    assert query == ne(PersonModel.first_name, "Michel")
    count = sync_engine.count(PersonModel, query)
    assert count == 2


@pytest.mark.usefixtures("person_persisted")
async def test_in_(aio_engine: AIOEngine):
    query = in_(PersonModel.first_name, ["Michel", "Jean-Pierre"])
    # TODO allow this with a mypy plugin
    assert query == PersonModel.first_name.in_(  # type: ignore
        ["Michel", "Jean-Pierre"]
    )
    count = await aio_engine.count(PersonModel, query)
    assert count == 3


@pytest.mark.usefixtures("person_persisted")
def test_sync_in_(sync_engine: SyncEngine):
    query = in_(PersonModel.first_name, ["Michel", "Jean-Pierre"])
    # TODO allow this with a mypy plugin
    assert query == PersonModel.first_name.in_(  # type: ignore
        ["Michel", "Jean-Pierre"]
    )
    count = sync_engine.count(PersonModel, query)
    assert count == 3


@pytest.mark.usefixtures("person_persisted")
async def test_not_in(aio_engine: AIOEngine):
    query = not_in(PersonModel.first_name, ["Michel", "Jean-Pierre"])
    # TODO allow this with a mypy plugin
    assert query == PersonModel.first_name.not_in(  # type: ignore
        ["Michel", "Jean-Pierre"]
    )
    count = await aio_engine.count(PersonModel, query)
    assert count == 0


@pytest.mark.usefixtures("person_persisted")
def test_sync_not_in(sync_engine: SyncEngine):
    query = not_in(PersonModel.first_name, ["Michel", "Jean-Pierre"])
    # TODO allow this with a mypy plugin
    assert query == PersonModel.first_name.not_in(  # type: ignore
        ["Michel", "Jean-Pierre"]
    )
    count = sync_engine.count(PersonModel, query)
    assert count == 0


class AgedPerson(Model):
    name: str
    age: int


@pytest.fixture(scope="function")
async def aged_person_persisted(aio_engine: AIOEngine):
    initial_instances = [
        AgedPerson(name="Jean-Pierre", age=25),
        AgedPerson(name="Jean-Paul", age=40),
        AgedPerson(name="Michel", age=70),
    ]
    return await aio_engine.save_all(initial_instances)


@pytest.mark.usefixtures("aged_person_persisted")
async def test_gt(aio_engine: AIOEngine):
    query = AgedPerson.age > 40
    assert query == AgedPerson.age.gt(40)  # type: ignore
    assert query == gt(AgedPerson.age, 40)
    count = await aio_engine.count(AgedPerson, query)
    assert count == 1


@pytest.mark.usefixtures("aged_person_persisted")
def test_sync_gt(sync_engine: SyncEngine):
    query = AgedPerson.age > 40
    assert query == AgedPerson.age.gt(40)  # type: ignore
    assert query == gt(AgedPerson.age, 40)
    count = sync_engine.count(AgedPerson, query)
    assert count == 1


@pytest.mark.usefixtures("aged_person_persisted")
async def test_gte(aio_engine: AIOEngine):
    query = AgedPerson.age >= 40
    assert query == AgedPerson.age.gte(40)  # type: ignore
    assert query == gte(AgedPerson.age, 40)
    count = await aio_engine.count(AgedPerson, query)
    assert count == 2


@pytest.mark.usefixtures("aged_person_persisted")
async def test_lt(aio_engine: AIOEngine):
    query = AgedPerson.age < 40
    assert query == AgedPerson.age.lt(40)  # type: ignore
    assert query == lt(AgedPerson.age, 40)
    count = await aio_engine.count(AgedPerson, query)
    assert count == 1


@pytest.mark.usefixtures("aged_person_persisted")
def test_sync_lt(sync_engine: SyncEngine):
    query = AgedPerson.age < 40
    assert query == AgedPerson.age.lt(40)  # type: ignore
    assert query == lt(AgedPerson.age, 40)
    count = sync_engine.count(AgedPerson, query)
    assert count == 1


@pytest.mark.usefixtures("aged_person_persisted")
async def test_lte(aio_engine: AIOEngine):
    query = AgedPerson.age <= 40
    assert query == AgedPerson.age.lte(40)  # type: ignore
    assert query == lte(AgedPerson.age, 40)
    count = await aio_engine.count(AgedPerson, query)
    assert count == 2


@pytest.mark.usefixtures("aged_person_persisted")
def test_sync_lte(sync_engine: SyncEngine):
    query = AgedPerson.age <= 40
    assert query == AgedPerson.age.lte(40)  # type: ignore
    assert query == lte(AgedPerson.age, 40)
    count = sync_engine.count(AgedPerson, query)
    assert count == 2


@pytest.mark.usefixtures("person_persisted")
async def test_match_pattern_string(aio_engine: AIOEngine):
    # TODO allow this with a mypy plugin
    query = PersonModel.first_name.match(r"^Jean-.*")  # type: ignore
    assert query == match(PersonModel.first_name, "^Jean-.*")
    count = await aio_engine.count(PersonModel, query)
    assert count == 2


@pytest.mark.usefixtures("person_persisted")
def test_sync_match_pattern_string(sync_engine: SyncEngine):
    # TODO allow this with a mypy plugin
    query = PersonModel.first_name.match(r"^Jean-.*")  # type: ignore
    assert query == match(PersonModel.first_name, "^Jean-.*")
    count = sync_engine.count(PersonModel, query)
    assert count == 2


@pytest.mark.usefixtures("person_persisted")
async def test_match_pattern_compiled(aio_engine: AIOEngine):
    # TODO allow this with a mypy plugin
    r = re.compile(r"^Jean-.*")
    query = PersonModel.first_name.match(r)  # type: ignore
    assert query == match(PersonModel.first_name, r)
    count = await aio_engine.count(PersonModel, query)
    assert count == 2


@pytest.mark.usefixtures("person_persisted")
def test_sync_match_pattern_compiled(sync_engine: SyncEngine):
    # TODO allow this with a mypy plugin
    r = re.compile(r"^Jean-.*")
    query = PersonModel.first_name.match(r)  # type: ignore
    assert query == match(PersonModel.first_name, r)
    count = sync_engine.count(PersonModel, query)
    assert count == 2
