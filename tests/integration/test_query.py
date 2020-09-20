from typing import cast

import pytest

from odmantic import Model
from odmantic.engine import AIOEngine
from odmantic.query import (
    QueryExpression,
    and_,
    eq,
    gt,
    gte,
    in_,
    lt,
    lte,
    ne,
    nor_,
    not_in,
    or_,
)

from ..zoo.person import PersonModel

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="function")
async def person_persisted(engine: AIOEngine):
    initial_instances = [
        PersonModel(first_name="Jean-Pierre", last_name="Pernaud"),
        PersonModel(first_name="Jean-Pierre", last_name="Castaldi"),
        PersonModel(first_name="Michel", last_name="Drucker"),
    ]
    return await engine.save_all(initial_instances)


@pytest.mark.usefixtures("person_persisted")
async def test_and(engine: AIOEngine):
    query = (PersonModel.first_name == "Michel") & (PersonModel.last_name == "Drucker")
    assert query == and_(
        PersonModel.first_name == "Michel", PersonModel.last_name == "Drucker"
    )
    count = await engine.count(PersonModel, query)
    assert count == 1


@pytest.mark.usefixtures("person_persisted")
async def test_or(engine: AIOEngine):
    query = (PersonModel.first_name == "Michel") | (PersonModel.last_name == "Castaldi")
    assert query == or_(
        PersonModel.first_name == "Michel", PersonModel.last_name == "Castaldi"
    )
    count = await engine.count(PersonModel, query)
    assert count == 2


@pytest.mark.usefixtures("person_persisted")
async def test_nor(engine: AIOEngine):
    count = await engine.count(
        PersonModel,
        nor_(PersonModel.first_name == "Michel", PersonModel.last_name == "Castaldi"),
    )
    assert count == 1


@pytest.mark.usefixtures("person_persisted")
async def test_eq(engine: AIOEngine):
    query = cast(QueryExpression, PersonModel.first_name == "Michel")
    assert query == eq(PersonModel.first_name, "Michel")
    count = await engine.count(PersonModel, query)
    assert count == 1


@pytest.mark.usefixtures("person_persisted")
async def test_ne(engine: AIOEngine):
    query = PersonModel.first_name != "Michel"
    assert query == ne(PersonModel.first_name, "Michel")
    count = await engine.count(PersonModel, query)
    assert count == 2


@pytest.mark.usefixtures("person_persisted")
async def test_in_(engine: AIOEngine):
    query = in_(PersonModel.first_name, ["Michel", "Jean-Pierre"])
    # TODO allow this with a mypy plugin
    assert query == PersonModel.first_name.in_(  # type: ignore
        ["Michel", "Jean-Pierre"]
    )
    count = await engine.count(PersonModel, query)
    assert count == 3


@pytest.mark.usefixtures("person_persisted")
async def test_not_in(engine: AIOEngine):
    query = not_in(PersonModel.first_name, ["Michel", "Jean-Pierre"])
    # TODO allow this with a mypy plugin
    assert query == PersonModel.first_name.not_in(  # type: ignore
        ["Michel", "Jean-Pierre"]
    )
    count = await engine.count(PersonModel, query)
    assert count == 0


class AgedPerson(Model):
    name: str
    age: int


@pytest.fixture(scope="function")
async def aged_person_persisted(engine: AIOEngine):
    initial_instances = [
        AgedPerson(name="Jean-Pierre", age=25),
        AgedPerson(name="Jean-Paul", age=40),
        AgedPerson(name="Michel", age=70),
    ]
    return await engine.save_all(initial_instances)


@pytest.mark.usefixtures("aged_person_persisted")
async def test_gt(engine: AIOEngine):
    query = AgedPerson.age > 40
    assert query == AgedPerson.age.gt(40)  # type: ignore
    assert query == gt(AgedPerson.age, 40)
    count = await engine.count(AgedPerson, query)
    assert count == 1


@pytest.mark.usefixtures("aged_person_persisted")
async def test_gte(engine: AIOEngine):
    query = AgedPerson.age >= 40
    assert query == AgedPerson.age.gte(40)  # type: ignore
    assert query == gte(AgedPerson.age, 40)
    count = await engine.count(AgedPerson, query)
    assert count == 2


@pytest.mark.usefixtures("aged_person_persisted")
async def test_lt(engine: AIOEngine):
    query = AgedPerson.age < 40
    assert query == AgedPerson.age.lt(40)  # type: ignore
    assert query == lt(AgedPerson.age, 40)
    count = await engine.count(AgedPerson, query)
    assert count == 1


@pytest.mark.usefixtures("aged_person_persisted")
async def test_lte(engine: AIOEngine):
    query = AgedPerson.age <= 40
    assert query == AgedPerson.age.lte(40)  # type: ignore
    assert query == lte(AgedPerson.age, 40)
    count = await engine.count(AgedPerson, query)
    assert count == 2
