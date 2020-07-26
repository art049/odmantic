import dataclasses
import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, Generic, List, Pattern, Tuple, Type, TypeVar

import pytest
from bson import Binary, Decimal128, Int64, ObjectId, Regex
from motor.motor_asyncio import AsyncIOMotorDatabase

from odmantic.engine import AIOEngine
from odmantic.model import Model
from odmantic.types import BSONSerializedField

pytestmark = pytest.mark.asyncio

T = TypeVar("T")


@dataclasses.dataclass
class TypeTestCase(Generic[T]):
    python_type: Type[T]
    bson_type: str
    sample_value: T


MIN_INT32 = -(2 ** 31)
UNDER_INT32_VALUE = MIN_INT32 - 1
MAX_INT32 = 2 ** 31 - 1
OVER_INT32_VALUE = MAX_INT32 + 1

sample_datetime = datetime.now()
sample_datetime = sample_datetime.replace(
    microsecond=10001
)  # Ensure we have some micro seconds that will be truncated
type_test_data = [
    TypeTestCase(int, "int", 15),
    TypeTestCase(int, "int", MIN_INT32),
    TypeTestCase(int, "int", MAX_INT32),
    TypeTestCase(int, "long", UNDER_INT32_VALUE),
    TypeTestCase(int, "long", OVER_INT32_VALUE),
    TypeTestCase(Int64, "long", 13),
    TypeTestCase(Int64, "long", Int64(13)),
    TypeTestCase(str, "string", "foo"),
    TypeTestCase(float, "double", 3.14),
    TypeTestCase(Decimal, "decimal", Decimal("3.14159265359")),
    TypeTestCase(
        Decimal, "decimal", "3.14159265359"
    ),  # TODO split tests for  odmantic type inference
    TypeTestCase(Decimal128, "decimal", Decimal128(Decimal("3.14159265359"))),
    TypeTestCase(Dict, "object", {"foo": "bar", "fizz": {"foo": "bar"}}),
    TypeTestCase(bool, "bool", False),
    TypeTestCase(Pattern, "regex", re.compile(r"^.*$")),
    TypeTestCase(Pattern, "regex", re.compile(r"^.*$", flags=re.IGNORECASE)),
    TypeTestCase(
        Pattern, "regex", re.compile(r"^.*$", flags=re.IGNORECASE | re.MULTILINE)
    ),
    TypeTestCase(Regex, "regex", Regex(r"^.*$", flags=32)),
    TypeTestCase(ObjectId, "objectId", ObjectId()),
    TypeTestCase(bytes, "binData", b"\xf0\xf1\xf2"),
    TypeTestCase(Binary, "binData", Binary(b"\xf0\xf1\xf2")),
    TypeTestCase(datetime, "date", sample_datetime),
    TypeTestCase(List, "array", ["one"]),
    TypeTestCase(Tuple[str, ...], "array", ("one",)),
]


@pytest.mark.parametrize("case", type_test_data)
async def test_bson_type_inference(
    motor_database: AsyncIOMotorDatabase, engine: AIOEngine, case: TypeTestCase
):
    class ModelWithTypedField(Model):
        field: case.python_type  # type: ignore

    # TODO: Fix objectid optional (type: ignore)
    instance = await engine.add(ModelWithTypedField(field=case.sample_value))
    document = await motor_database[ModelWithTypedField.__collection__].find_one(
        {
            +ModelWithTypedField.id: instance.id,  # type: ignore
            +ModelWithTypedField.field: {"$type": case.bson_type},
        }
    )
    assert document is not None, (
        f"Type inference error: {case.python_type} -> {case.bson_type}"
        f" ({case.sample_value})"
    )
    print(document, str(document["field"]))
    recovered_instance = ModelWithTypedField(field=document["field"])
    assert recovered_instance.field == instance.field


async def test_custom_bson_serializable(
    motor_database: AsyncIOMotorDatabase, engine: AIOEngine
):
    class FancyFloat(BSONSerializedField):
        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v):
            return float(v)

        @classmethod
        def to_bson(cls, v):
            # We store the float as a string in the DB
            return str(v)

    class ModelWithCustomField(Model):
        field: FancyFloat

    instance = await engine.add(ModelWithCustomField(field=3.14))
    document = await motor_database[ModelWithCustomField.__collection__].find_one(
        {
            +ModelWithCustomField.id: instance.id,  # type: ignore
            +ModelWithCustomField.field: {"$type": "string"},
        }
    )
    assert document is not None, "Couldn't retrieve the document with it's string value"
    recovered_instance = ModelWithCustomField.parse_doc(document)
    assert recovered_instance.field == instance.field
