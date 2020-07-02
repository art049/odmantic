from bson import ObjectId as BsonObjectId
from bson.binary import Binary as BsonBinary
from bson.decimal128 import Decimal128 as BsonDecimal
from bson.int64 import Int64 as BsonLong
from bson.regex import Regex as BsonRegex
from pydantic.validators import (
    bytes_validator,
    decimal_validator,
    int_validator,
    pattern_validator,
)


class _objectId(BsonObjectId):
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


_SUBSTITUTION_TYPES = {
    BsonObjectId: _objectId,
    BsonLong: _long,
    BsonDecimal: _decimal,
    BsonBinary: _binary,
    BsonRegex: _regex,
}
