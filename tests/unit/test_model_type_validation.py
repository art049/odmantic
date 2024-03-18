import sys
from typing import (
    Callable,
    Dict,
    FrozenSet,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)

import bson
import pytest
from typing_utils import are_generics_equal

from odmantic.bson import (
    _BSON_SUBSTITUTED_FIELDS,
    Binary,
    Decimal128,
    Int64,
    ObjectId,
    Regex,
)
from odmantic.model import EmbeddedModel, Model, is_type_mutable, validate_type


@pytest.mark.parametrize("base, replacement", _BSON_SUBSTITUTED_FIELDS.items())
def test_validate_type_bson_substituted(base, replacement):
    assert validate_type(base) == replacement


@pytest.mark.parametrize("base, replacement", _BSON_SUBSTITUTED_FIELDS.items())
def test_optional_bson_subst(base, replacement):
    assert are_generics_equal(
        validate_type(Optional[base]),
        Optional[replacement],
    )


@pytest.mark.parametrize("origin", (List, Set, FrozenSet, Sequence))
@pytest.mark.parametrize("base, replacement", _BSON_SUBSTITUTED_FIELDS.items())
def test_single_arg_type_bson_subst(origin, base, replacement):
    assert are_generics_equal(validate_type(origin[base]), origin[replacement])


def test_forbidden_field():
    with pytest.raises(TypeError, match="fields are not supported"):
        validate_type(Callable)  # type: ignore


def test_deep_nest_bson_subst():
    assert are_generics_equal(
        validate_type(
            Union[  # type: ignore
                Dict[List[bson.ObjectId], Dict[bson.ObjectId, bson.Decimal128]],
                Dict[Dict[Set[bson.Int64], bson.Binary], Tuple[bson.Regex, ...]],
            ]
        ),
        Union[
            Dict[List[ObjectId], Dict[ObjectId, Decimal128]],
            Dict[Dict[Set[Int64], Binary], Tuple[Regex, ...]],
        ],
    )


class DummyEmbedded(EmbeddedModel):
    field: str


class DummyModel(Model):
    field: str


@pytest.mark.parametrize(
    "t",
    (
        None,
        bool,
        int,
        str,
        Tuple,
        Tuple[int, str, bool],
        Tuple[int, ...],
        FrozenSet[int],
        Union[FrozenSet[int], Tuple[int, str]],
        DummyModel,
    ),
)
def test_mutable_types_immutables(t: Type):
    assert not is_type_mutable(t)


TEST_TYPES = [
    List,
    Set,
    List[int],
    Tuple[List[int]],
    FrozenSet[Set[int]],
    Dict[Tuple[int, ...], str],
    DummyEmbedded,
    Tuple[DummyEmbedded, ...],
    Dict[str, DummyEmbedded],
    FrozenSet[DummyEmbedded],
]

# if generic with builtin types are supported add them to the list
if sys.version_info >= (3, 9):
    TEST_TYPES += [
        list,
        set,
        list[int],
        tuple[list[int]],
        frozenset[set[int]],
        dict[tuple[int, ...], str],
    ]


@pytest.mark.parametrize(
    "t",
    TEST_TYPES,
)
def test_mutable_types_mutables(t: Type):
    assert is_type_mutable(t)


def test_mutable_types_unknown_type():
    class T: ...

    assert is_type_mutable(T)


def test_mutable_field_embedded_model():
    class E(EmbeddedModel):
        f: int

    class M(Model):
        e: E

    assert "e" in M.__mutable_fields__
