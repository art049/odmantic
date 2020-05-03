from typing import Any, Optional

from bson import ObjectId as BsonObjectId


class _MISSING_TYPE:
    pass


MISSING_DEFAULT = _MISSING_TYPE()


def field(**kwargs) -> Any:
    return Field(**kwargs)


class Field:
    """Class providing mongodb field customization
    """

    def __init__(
        self,
        *,
        primary_key: bool = False,
        mongo_name: Optional[str] = None,
        default=MISSING_DEFAULT
    ):
        if primary_key:
            assert (
                mongo_name is None
            ), "Setting primary key enforce the mongo_name to _id"

        self.primary_key = primary_key
        self.mongo_name = mongo_name
        self.default = default


class ObjectId(BsonObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, (BsonObjectId, ObjectId)):
            raise TypeError("ObjectId required")
        # TODO object ids from strings
        return v
