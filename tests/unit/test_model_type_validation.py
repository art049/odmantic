from typing import (
    Callable,
    Dict,
    FrozenSet,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import pytest
from bson.binary import Binary
from bson.decimal128 import Decimal128
from bson.int64 import Int64
from bson.objectid import ObjectId
from bson.regex import Regex

from odmantic.bson_fields import (
    _BSON_SUBSTITUTED_FIELDS,
    _binary,
    _bson_decimal,
    _long,
    _objectId,
    _regex,
)
from odmantic.model import validate_type


@pytest.mark.parametrize("base, replacement", _BSON_SUBSTITUTED_FIELDS.items())
def test_validate_type_bson_substituted(base, replacement):
    assert validate_type(base) == replacement


@pytest.mark.parametrize("base, replacement", _BSON_SUBSTITUTED_FIELDS.items())
def test_optional_bson_subst(base, replacement):
    assert validate_type(Optional[base]) == Optional[replacement]  # type: ignore


@pytest.mark.parametrize("origin", (List, Set, FrozenSet, Sequence))
@pytest.mark.parametrize("base, replacement", _BSON_SUBSTITUTED_FIELDS.items())
def test_single_arg_type_bson_subst(origin, base, replacement):
    assert validate_type(origin[base]) == origin[replacement]


def test_forbidden_field():
    with pytest.raises(TypeError, match="fields are not supported"):
        validate_type(Callable)  # type: ignore


def test_deep_nest_bson_subst():
    assert (
        validate_type(
            Union[  # type: ignore
                Dict[List[ObjectId], Dict[ObjectId, Decimal128]],
                Dict[Dict[Set[Int64], Binary], Tuple[Regex, ...]],
            ]
        )
        == Union[
            Dict[List[_objectId], Dict[_objectId, _bson_decimal]],
            Dict[Dict[Set[_long], _binary], Tuple[_regex, ...]],
        ]
    )
