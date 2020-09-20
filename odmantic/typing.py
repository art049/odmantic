import sys
from typing import Any, Dict, Sequence, Union

from bson import ObjectId
from bson.binary import Binary
from bson.decimal128 import Decimal128
from bson.int64 import Int64
from bson.regex import Regex

if sys.version_info < (3, 7):
    from typing import Callable as Callable

    NoArgAnyCallable = Callable[[], Any]
else:
    from collections.abc import Callable as Callable
    from typing import Callable as TypingCallable

    NoArgAnyCallable = TypingCallable[[], Any]


BSON_TYPE = Union[
    str, int, float, ObjectId, Decimal128, Int64, Regex, Binary, Dict, Sequence
]
