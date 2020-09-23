from bson.binary import Binary
from bson.decimal128 import Decimal128
from bson.int64 import Int64
from bson.objectid import ObjectId
from bson.regex import Regex

from odmantic.model import Model


class FullBsonModel(Model):
    """Model used to test BSON types"""

    objectId_: ObjectId
    long_: Int64
    decimal_: Decimal128
    binary_: Binary
    regex_: Regex
