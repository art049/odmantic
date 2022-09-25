import dataclasses
import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Generic, List, Pattern, Tuple, Type, TypeVar, Union

import pytest
from bson import Binary, Decimal128, Int64, ObjectId, Regex
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

from odmantic.engine import AIOEngine, SyncEngine
from odmantic.model import Model

pytestmark = pytest.mark.asyncio

T = TypeVar("T")


@dataclasses.dataclass
class TypeTestCase(Generic[T]):
    python_type: Type[T]
    bson_type: str
    sample_value: T


MIN_INT32 = -(2**31)
UNDER_INT32_VALUE = MIN_INT32 - 1
MAX_INT32 = 2**31 - 1
OVER_INT32_VALUE = MAX_INT32 + 1

sample_datetime = datetime.now()

type_test_data = [
    # Simple types
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
    TypeTestCase(Dict[str, Any], "object", {"foo": "bar", "fizz": {"foo": "bar"}}),
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
    TypeTestCase(List[str], "array", ["one"]),
    # Compound Types
    TypeTestCase(Tuple[str, ...], "array", ("one",)),  # type: ignore
    TypeTestCase(List[ObjectId], "array", [ObjectId() for _ in range(5)]),
    TypeTestCase(
        Union[Tuple[ObjectId, ...], None],  # type: ignore
        "array",
        tuple(ObjectId() for _ in range(5)),
    ),
]


@pytest.mark.parametrize("case", type_test_data)
async def test_bson_type_inference(
    motor_database: AsyncIOMotorDatabase, aio_engine: AIOEngine, case: TypeTestCase
):
    class ModelWithTypedField(Model):
        field: case.python_type  # type: ignore

    # TODO: Fix objectid optional (type: ignore)
    instance = await aio_engine.save(ModelWithTypedField(field=case.sample_value))
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
    recovered_instance = ModelWithTypedField(field=document["field"])
    assert recovered_instance.field == instance.field


@pytest.mark.parametrize("case", type_test_data)
def test_sync_bson_type_inference(
    pymongo_database: Database, sync_engine: SyncEngine, case: TypeTestCase
):
    class ModelWithTypedField(Model):
        field: case.python_type  # type: ignore

    # TODO: Fix objectid optional (type: ignore)
    instance = sync_engine.save(ModelWithTypedField(field=case.sample_value))
    document = pymongo_database[ModelWithTypedField.__collection__].find_one(
        {
            +ModelWithTypedField.id: instance.id,  # type: ignore
            +ModelWithTypedField.field: {"$type": case.bson_type},
        }
    )
    assert document is not None, (
        f"Type inference error: {case.python_type} -> {case.bson_type}"
        f" ({case.sample_value})"
    )
    recovered_instance = ModelWithTypedField(field=document["field"])
    assert recovered_instance.field == instance.field


async def test_custom_bson_serializable(
    motor_database: AsyncIOMotorDatabase, aio_engine
):
    class FancyFloat:
        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v):
            return float(v)

        @classmethod
        def __bson__(cls, v):
            # We store the float as a string in the DB
            return str(v)

    class ModelWithCustomField(Model):
        field: FancyFloat

    instance = await aio_engine.save(ModelWithCustomField(field=3.14))
    document = await motor_database[ModelWithCustomField.__collection__].find_one(
        {
            +ModelWithCustomField.id: instance.id,  # type: ignore
            +ModelWithCustomField.field: {"$type": "string"},  # type: ignore
        }
    )
    assert document is not None, "Couldn't retrieve the document with it's string value"
    recovered_instance = ModelWithCustomField.parse_doc(document)
    assert recovered_instance.field == instance.field


def test_sync_custom_bson_serializable(
    pymongo_database: Database, sync_engine: SyncEngine
):
    class FancyFloat:
        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v):
            return float(v)

        @classmethod
        def __bson__(cls, v):
            # We store the float as a string in the DB
            return str(v)

    class ModelWithCustomField(Model):
        field: FancyFloat

    instance = sync_engine.save(ModelWithCustomField(field=3.14))
    document = pymongo_database[ModelWithCustomField.__collection__].find_one(
        {
            +ModelWithCustomField.id: instance.id,  # type: ignore
            +ModelWithCustomField.field: {"$type": "string"},  # type: ignore
        }
    )
    assert document is not None, "Couldn't retrieve the document with it's string value"
    recovered_instance = ModelWithCustomField.parse_doc(document)
    assert recovered_instance.field == instance.field
