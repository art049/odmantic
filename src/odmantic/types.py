from bson import ObjectId as BsonObjectId
from bson.binary import Binary as BsonBinary
from bson.decimal128 import Decimal128 as BsonDecimal
from bson.int64 import Int64 as BsonLong
from pydantic.validators import bytes_validator, decimal_validator, int_validator


class objectId(BsonObjectId):
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


class long(BsonLong):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, (BsonLong, cls)):
            return v
        a = int_validator(v)  # Todo change error behavior
        return cls(a)


class decimal(BsonDecimal):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, (BsonLong, cls)):
            return v
        a = decimal_validator(v)  # Todo change error behavior
        return cls(a)
