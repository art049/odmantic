import re
from abc import ABCMeta, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Pattern

from bson import ObjectId as BsonObjectId
from bson.binary import Binary as BsonBinary
from bson.decimal128 import Decimal128 as BsonDecimal
from bson.int64 import Int64 as BsonLong
from bson.regex import Regex as BsonRegex
from pydantic.datetime_parse import parse_datetime
from pydantic.validators import (
    bytes_validator,
    decimal_validator,
    int_validator,
    pattern_validator,
)


class _objectId(BsonObjectId):
    # TODO fix this behavior different from others subst
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, (BsonObjectId, cls)):
            return v
        if isinstance(v, str) and BsonObjectId.is_valid(v):
            return BsonObjectId(v)
        raise TypeError("ObjectId required")  # Todo change error behavior

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="ObjectId")


class _long:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, BsonLong):
            return v
        a = int_validator(v)  # Todo change error behavior
        return BsonLong(a)


class _decimal:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, BsonDecimal):
            return v
        a = decimal_validator(v)  # Todo change error behavior
        return BsonDecimal(a)


class _binary:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, BsonBinary):
            return v
        a = bytes_validator(v)  # Todo change error behavior
        return BsonBinary(a)


class _regex:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, BsonRegex):
            return v
        a = pattern_validator(v)  # Todo change error behavior
        return BsonRegex(a)


class _Pattern:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, Pattern):
            return v
        elif isinstance(v, BsonRegex):
            return re.compile(v.pattern, flags=v.flags)

        a = pattern_validator(v)  # Todo change error behavior
        return a


class _datetime:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, datetime):
            d = v
        else:
            d = parse_datetime(v)  # Todo change error behavior
        # MongoDB does not store timezone info
        # https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
        if d.tzinfo is not None and d.tzinfo.utcoffset(d) is not None:
            raise ValueError("datetime objects must be naive (no timeone info)")
        # Round microseconds to the nearest millisecond to comply with Mongo behavior
        microsecs = round(d.microsecond / 1000) * 1000
        return d.replace(microsecond=microsecs)


class BSONSerializedField(metaclass=ABCMeta):
    @abstractmethod
    def to_bson(cls, v):
        """This should be overridden with a class method"""

    def __pos__(self):
        """Only here to help mypy"""
        # TODO: handle this in a plugin


class _Decimal(BSONSerializedField):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, Decimal):
            return v
        elif isinstance(v, BsonDecimal):
            return v.to_decimal()

        a = decimal_validator(v)  # Todo change error behavior
        return a

    @classmethod
    def to_bson(cls, v):
        return BsonDecimal(v)


_SUBSTITUTION_TYPES = {
    BsonObjectId: _objectId,
    BsonLong: _long,
    BsonDecimal: _decimal,
    BsonBinary: _binary,
    BsonRegex: _regex,
    Pattern: _Pattern,
    Decimal: _Decimal,
    datetime: _datetime,
}
