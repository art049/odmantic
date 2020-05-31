import dataclasses
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Generic, Pattern, Type, TypeVar

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase

from odmantic.model import Model
from odmantic.session import AIOSession
from odmantic.types import decimal, long, objectId

pytestmark = pytest.mark.asyncio

T = TypeVar("T")


@dataclasses.dataclass
class TypeTestCase(Generic[T]):
    python_type: Type[T]
    bson_type: str
    sample_value: T


OVER_INT32_VALUE = 2 ** 32

type_test_data = [
    TypeTestCase(int, "int", 15),
    TypeTestCase(int, "long", OVER_INT32_VALUE),
    TypeTestCase(long, "long", 13),
    TypeTestCase(str, "string", "foo"),
    TypeTestCase(float, "double", 3.14),
    TypeTestCase(decimal, "decimal", Decimal("3.14159265359")),
    TypeTestCase(Dict, "object", {"foo": "bar", "fizz": {"foo": "bar"}}),
    TypeTestCase(bool, "bool", False),
    TypeTestCase(Pattern, "regex", r"^.*$"),
    TypeTestCase(objectId, "objectId", objectId()),
    TypeTestCase(bytes, "binData", b"\xf0\xf1\xf2"),
    TypeTestCase(datetime, "date", datetime.now()),
    TypeTestCase(datetime, "date", datetime.now(timezone.utc)),
]


@pytest.mark.parametrize("case", type_test_data)
async def test_type_inference(
    motor_database: AsyncIOMotorDatabase, session: AIOSession, case: TypeTestCase
):
    class ModelWithTypedField(Model):
        field: case.python_type

    instance = await session.add(ModelWithTypedField(field=case.sample_value))
    n = await motor_database[ModelWithTypedField.__collection__].count_documents(
        {
            +ModelWithTypedField.id: instance.id,
            +ModelWithTypedField.field: {"$type": case.bson_type},
        }
    )
    assert n == 1, f"Type inference error: {case.python_type} -> {case.bson_type}"
