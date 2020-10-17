import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Pattern, cast

from bson.binary import Binary as BsonBinary
from bson.decimal128 import Decimal128 as BsonDecimal
from bson.int64 import Int64 as BsonLong
from bson.objectid import ObjectId as BsonObjectId
from bson.regex import Regex as BsonRegex
from pydantic.datetime_parse import parse_datetime
from pydantic.main import BaseModel
from pydantic.validators import (
    bytes_validator,
    decimal_validator,
    int_validator,
    pattern_validator,
)


class _objectId(BsonObjectId):
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> BsonObjectId:
        if isinstance(v, (BsonObjectId, cls)):
            return v
        if isinstance(v, str) and BsonObjectId.is_valid(v):
            return BsonObjectId(v)
        raise TypeError("invalid ObjectId specified")


class _long:
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> BsonLong:
        if isinstance(v, BsonLong):
            return v
        a = int_validator(v)
        return BsonLong(a)


class _bson_decimal:
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> BsonDecimal:
        if isinstance(v, BsonDecimal):
            return v
        a = decimal_validator(v)
        return BsonDecimal(a)


class _binary:
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> BsonBinary:
        if isinstance(v, BsonBinary):
            return v
        a = bytes_validator(v)
        return BsonBinary(a)


class _regex:
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> BsonRegex:
        if isinstance(v, BsonRegex):
            return v
        a = pattern_validator(v)
        return BsonRegex(a.pattern)


class _Pattern:
    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> Pattern:
        if isinstance(v, Pattern):
            return v
        elif isinstance(v, BsonRegex):
            return re.compile(v.pattern, flags=v.flags)

        a = pattern_validator(v)
        return a


class _datetime:
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
        if d.tzinfo is not None and d.tzinfo.utcoffset(d) is not None:
            raise ValueError("datetime objects must be naive (no timeone info)")
        # Round microseconds to the nearest millisecond to comply with Mongo behavior
        microsecs = round(d.microsecond / 1000) * 1000
        return d.replace(microsecond=microsecs)


class _Decimal:
    """This specific BSON substitution field helps to handle the support of standard
    python Decimal objects

    https://api.mongodb.com/python/current/faq.html?highlight=decimal#how-can-i-store-decimal-decimal-instances
    """

    @classmethod
    def __get_validators__(cls):  # type: ignore
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> Decimal:
        if isinstance(v, Decimal):
            return v
        elif isinstance(v, BsonDecimal):
            return cast(Decimal, v.to_decimal())

        a = decimal_validator(v)
        return a

    @classmethod
    def __bson__(cls, v: Any) -> BsonDecimal:
        return BsonDecimal(v)


_BSON_TYPES_ENCODERS = {
    BsonObjectId: str,
    BsonDecimal: lambda x: x.to_decimal(),  # Convert to regular decimal
    BsonRegex: lambda x: x.pattern,  # TODO: document no serialization of flags
}


class BaseBSONModel(BaseModel):
    class Config:
        json_encoders = _BSON_TYPES_ENCODERS


_BSON_SUBSTITUTED_FIELDS = {
    BsonObjectId: _objectId,
    BsonLong: _long,
    BsonDecimal: _bson_decimal,
    BsonBinary: _binary,
    BsonRegex: _regex,
    Pattern: _Pattern,
    Decimal: _Decimal,
    datetime: _datetime,
}
