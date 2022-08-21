import decimal
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Pattern

import bson
import bson.binary
import bson.decimal128
import bson.int64
import bson.regex
from pydantic.datetime_parse import parse_datetime
from pydantic.main import BaseModel
from pydantic.validators import (
    bytes_validator,
    decimal_validator,
    int_validator,
    pattern_validator,
)


class ObjectId(bson.ObjectId):
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict) -> None:
        field_schema.update(
            examples=["5f85f36d6dfecacc68428a46", "ffffffffffffffffffffffff"],
            example="5f85f36d6dfecacc68428a46",
            type="string",
        )

    @classmethod
    def validate(cls, v: Any) -> bson.ObjectId:
        if isinstance(v, (bson.ObjectId, cls)):
            return v
        if isinstance(v, str) and bson.ObjectId.is_valid(v):
            return bson.ObjectId(v)
        raise TypeError("invalid ObjectId specified")


class Int64(bson.int64.Int64):
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict) -> None:
        field_schema.update(examples=[2147483649], type="number")

    @classmethod
    def validate(cls, v: Any) -> bson.int64.Int64:
        if isinstance(v, bson.int64.Int64):
            return v
        a = int_validator(v)
        return bson.int64.Int64(a)


Long = Int64


class Decimal128(bson.decimal128.Decimal128):
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict) -> None:
        field_schema.update(examples=[214.7483649], example=214.7483649, type="number")

    @classmethod
    def validate(cls, v: Any) -> bson.decimal128.Decimal128:
        if isinstance(v, bson.decimal128.Decimal128):
            return v
        a = decimal_validator(v)
        return bson.decimal128.Decimal128(a)


class Binary(bson.binary.Binary):
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict) -> None:
        field_schema.update(type="string", format="binary")

    @classmethod
    def validate(cls, v: Any) -> bson.binary.Binary:
        if isinstance(v, bson.binary.Binary):
            return v
        a = bytes_validator(v)
        return bson.binary.Binary(a)


class Regex(bson.regex.Regex):
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict) -> None:
        field_schema.update(
            examples=[r"^Foo"], example=r"^Foo", type="string", format="binary"
        )

    @classmethod
    def validate(cls, v: Any) -> bson.regex.Regex:
        if isinstance(v, bson.regex.Regex):
            return v
        a = pattern_validator(v)
        return bson.regex.Regex(a.pattern)


class _Pattern:
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> Pattern:
        if isinstance(v, Pattern):
            return v
        elif isinstance(v, bson.regex.Regex):
            return re.compile(v.pattern, flags=v.flags)

        a = pattern_validator(v)
        return a


class _datetime(datetime):
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            d = v
        else:
            d = parse_datetime(v)
        # MongoDB does not store timezone info
        # https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
        if d.tzinfo is not None and d.tzinfo.utcoffset(d) != timedelta(0):
            raise ValueError("datetime objects must be naive (no timezone info)")
        # Truncate microseconds to milliseconds to comply with Mongo behavior
        microsecs = d.microsecond - d.microsecond % 1000
        return d.replace(microsecond=microsecs)

    @classmethod
    def __modify_schema__(cls, field_schema: Dict) -> None:
        field_schema.update(example=datetime.utcnow().isoformat())


class _decimalDecimal(decimal.Decimal):
    """This specific BSON substitution field helps to handle the support of standard
    python Decimal objects

    https://api.mongodb.com/python/current/faq.html?highlight=decimal#how-can-i-store-decimal-decimal-instances
    """

    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> decimal.Decimal:
        if isinstance(v, decimal.Decimal):
            return v
        elif isinstance(v, bson.decimal128.Decimal128):
            return v.to_decimal()

        a = decimal_validator(v)
        return a

    @classmethod
    def __bson__(cls, v: Any) -> bson.decimal128.Decimal128:
        return bson.decimal128.Decimal128(v)


BSON_TYPES_ENCODERS = {
    bson.ObjectId: str,
    bson.decimal128.Decimal128: lambda x: x.to_decimal(),  # Convert to regular decimal
    bson.regex.Regex: lambda x: x.pattern,  # TODO: document no serialization of flags
}


class BaseBSONModel(BaseModel):
    """Equivalent of `pydantic.BaseModel` supporting BSON types encoding.

    If you want to apply other custom JSON encoders, you'll need to use
    [BSON_TYPES_ENCODERS][odmantic.bson.BSON_TYPES_ENCODERS] directly.
    """

    class Config:
        json_encoders = BSON_TYPES_ENCODERS


_BSON_SUBSTITUTED_FIELDS = {
    bson.ObjectId: ObjectId,
    bson.int64.Int64: Int64,
    bson.decimal128.Decimal128: Decimal128,
    bson.binary.Binary: Binary,
    bson.regex.Regex: Regex,
    Pattern: _Pattern,
    decimal.Decimal: _decimalDecimal,
    datetime: _datetime,
}
