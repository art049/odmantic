import sys
from types import FunctionType
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    FrozenSet,
    List,
    Literal,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import pytest
from bson import ObjectId
from bson.decimal128 import Decimal128
from bson.regex import Regex
from pydantic import Field as PDField
from pydantic import ValidationError

from odmantic import ObjectId as ODMObjectId
from odmantic.field import Field
from odmantic.model import EmbeddedModel, Model
from odmantic.reference import Reference


class TheClassName(Model): ...


class TheClassNameModel(Model): ...


class TheClassNameOverriden(Model):
    model_config = {"collection": "collection_name"}


def test_auto_collection_name():
    assert TheClassName.__collection__ == "the_class_name"

    assert TheClassNameModel.__collection__ == "the_class_name"

    assert TheClassNameOverriden.__collection__ == "collection_name"


def test_auto_collection_name_nested():
    class theNestedClassName(Model): ...

    assert theNestedClassName.__collection__ == "the_nested_class_name"

    class TheNestedClassNameOverriden(Model):
        model_config = {"collection": "collection_name"}

    assert TheNestedClassNameOverriden.__collection__ == "collection_name"


def test_get_collection_name_pos():
    class Thing(Model): ...

    assert +Thing == "thing"


def test_duplicated_key_name():
    with pytest.raises(TypeError):

        class M(Model):
            a: int
            b: int = Field(key_name="a")


def test_duplicated_key_name_in_reference():
    class Referenced(Model):
        a: int

    with pytest.raises(TypeError):

        class Base(Model):
            a: int = Field(key_name="referenced")
            referenced: Referenced = Reference()


def test_duplicate_key_name_definition():
    with pytest.raises(TypeError):

        class Base(Model):
            a: int = Field(key_name="referenced")
            b: int = Field(key_name="referenced")


def test_key_name_containing_dollar_sign():
    class Base(Model):
        a: int = Field(key_name="a$b")


def test_key_starting_with_dollar_sign():
    with pytest.raises(TypeError):

        class Base(Model):
            a: int = Field(key_name="$a")


def test_key_containing_dot():
    with pytest.raises(TypeError):

        class Base(Model):
            b: int = Field(key_name="a.b")


def test_wrong_model_field():
    with pytest.raises(TypeError, match="use odmantic.Field instead of pydantic.Field"):

        class M(Model):
            a: int = PDField()


def test_unknown_model_field():
    class UnknownType:
        pass

    def U() -> Any:
        return UnknownType()

    with pytest.raises(TypeError):

        class M(Model):
            a: int = U()


def test_model_default_simple():
    class M(Model):
        f: int = 3

    instance = M()
    assert instance.f == 3


def test_model_default_with_field():
    class M(Model):
        f: int = Field(default=3)

    instance = M()
    assert instance.f == 3


def test_optional_field_with_default():
    class M(Model):
        f: Optional[str] = None

    assert M().f is None
    assert M(f="hello world").f == "hello world"


def test_field_with_invalid_default_type():
    with pytest.raises(TypeError, match="Unhandled field definition"):

        class M(Model):
            f: Optional[int] = "a"  # type: ignore


@pytest.mark.skip("Wait for feedback on an pydantic issue #1936")
def test_field_with_invalid_default_type_in_field():
    with pytest.raises(TypeError, match="Unhandled field definition"):

        class M(Model):
            f: Optional[int] = Field("a")


@pytest.mark.skip("Wait for feedback on an pydantic issue #1936")
def test_field_with_invalid_default_value_in_field_at_definition():
    with pytest.raises(TypeError, match="Unhandled field definition"):

        class M(Model):
            f: Optional[int] = Field(3, gt=5)


def test_field_with_invalid_default_value_in_field_at_instantiation():
    class M(Model):
        f: Optional[int] = Field(3, gt=5)

    with pytest.raises(ValidationError):
        M()


def test_optional_field_with_field_settings():
    class M(Model):
        f: Optional[str] = Field("hello world", key_name="my_field")

    assert M().f == "hello world"
    assert M(f=None).f is None


def test_unable_to_generate_primary_field():
    with pytest.raises(TypeError, match="can't automatically generate a primary field"):

        class A(Model):
            id: str


def test_define_alternate_primary_key():
    class M(Model):
        name: str = Field(primary_field=True)

    instance = M(name="Jack")
    assert instance.model_dump_doc() == {"_id": "Jack"}


def test_weird_overload_id_field():
    class M(Model):
        id: int
        name: str = Field(primary_field=True)

    instance = M(id=15, name="Johnny")
    assert instance.model_dump_doc() == {"_id": "Johnny", "id": 15}


@pytest.mark.skip("Not implemented, see if it should be supported...")
def test_overload_id_with_another_primary_key():
    with pytest.raises(TypeError, match="cannot define multiple primary keys"):

        class M(Model):
            id: int
            number: int = Field(primary_key=True)


def test_untyped_field_definition():
    with pytest.raises(TypeError, match="defined without type annotation"):

        class M(Model):
            a = 3


def test_multiple_primary_key():
    with pytest.raises(TypeError, match="Duplicated key_name"):

        class M(Model):
            a: int = Field(primary_field=True)
            b: int = Field(primary_field=True)


def test_model_with_implicit_reference_error():
    class A(Model):
        pass

    with pytest.raises(TypeError, match="without a Reference assigned"):

        class B(Model):
            a: A


def test_embedded_model_with_primary_key():
    with pytest.raises(TypeError, match="cannot define a primary field"):

        class A(EmbeddedModel):
            f: int = Field(primary_field=True)


T = TypeVar("T")


@pytest.mark.parametrize("generic", [List, Set, Tuple])
def test_embedded_model_generics_as_primary_key(generic: Type):
    class E(EmbeddedModel):
        f: int

    with pytest.raises(
        TypeError,
        match="Declaring a generic type of embedded models as a primary field"
        " is not allowed",
    ):

        class M(Model):
            e: generic[E] = Field(primary_field=True)  # type: ignore


@pytest.mark.parametrize(
    "generic",
    [
        lambda e: List[e],  # type: ignore
        lambda e: Set[e],  # type: ignore
        lambda e: Dict[str, e],  # type: ignore
        lambda e: Tuple[e],
        lambda e: Tuple[e, ...],
    ],
)
def test_embedded_model_generics_with_references(generic: Callable[[Type], Type]):
    class AnotherModel(Model):
        a: float

    class E(EmbeddedModel):
        f: AnotherModel = Reference()

    with pytest.raises(
        TypeError,
        match="Declaring a generic type of embedded models containing references"
        " is not allowed",
    ):

        class M(Model):
            e: generic(E)  # type: ignore


def test_invalid_collection_name_dollar():
    with pytest.raises(TypeError, match=r"cannot contain '\$'"):

        class A(Model):
            model_config = {"collection": "hello$world"}


def test_invalid_collection_name_empty():
    with pytest.raises(TypeError, match="cannot be empty"):

        class A(Model):
            model_config = {"collection": ""}


def test_invalid_collection_name_contain_system_dot():
    with pytest.raises(TypeError, match="cannot start with 'system.'"):

        class A(Model):
            model_config = {"collection": "system.hi"}


def test_custom_collection_name():
    class M(Model):
        model_config = {"collection": "collection_name"}

    assert M.__collection__ == "collection_name"


def test_embedded_model_key_name():
    class E(EmbeddedModel):
        f: int = 3

    class M(Model):
        field: E = Field(E(), key_name="hello")

    doc = M().model_dump_doc()
    assert "hello" in doc
    assert doc["hello"] == {"f": 3}


def test_embedded_model_as_primary_field():
    class E(EmbeddedModel):
        f: int

    class M(Model):
        field: E = Field(primary_field=True)

    assert M(field=E(f=1)).model_dump_doc() == {"_id": {"f": 1}}


def test_untouched_types_function():
    def id_str(self) -> str:  # pragma: no cover
        return str(self.id)

    class M(Model):
        model_config = {"arbitrary_types_allowed": True}

        id_: FunctionType = id_str  # type: ignore

    assert "id_" not in M.__odm_fields__.keys()


@pytest.mark.parametrize(
    "t",
    [
        Optional[ObjectId],
        List[ObjectId],
        List[Decimal128],
        List[Regex],
        FrozenSet[Regex],
        Union[Regex, ObjectId],
        Dict[ObjectId, str],
        Dict[Tuple[ObjectId, ...], str],
        Dict[Union[ObjectId, str], str],
        Mapping[Union[ObjectId, str], str],
    ],
)
def test_compound_bson_field(t: Type):
    class M(Model):
        children: t  # type: ignore


def test_forbidden_field():
    with pytest.raises(TypeError, match="fields are not supported"):

        class M(Model):
            children: Callable


def test_model_with_class_var():
    class M(Model):
        cls_var: ClassVar[str] = "theclassvar"
        field: int

    assert M.cls_var == "theclassvar"
    m = M(field=5)
    assert m.cls_var == "theclassvar"
    assert m.field == 5
    assert "cls_var" not in m.model_dump_doc().keys()


def test_model_definition_extra_allow():
    class M(Model):
        model_config = {"extra": "allow"}

        f: int

    instance = M(f=1, g=2)
    assert instance.model_dump_doc(include={"f", "g"}) == {"f": 1, "g": 2}


def test_model_definition_extra_ignore():
    class M(Model):
        model_config = {"extra": "ignore"}

        f: int

    instance = M(f=1, g=2)
    assert instance.model_dump_doc(include={"f", "g"}) == {"f": 1}


def test_model_definition_extra_forbid():
    class M(Model):
        model_config = {"extra": "forbid"}

        f: int

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        M(f=1, g=2)


def test_extra_field_type_subst():
    class M(Model):
        model_config = {"extra": "allow"}

        f: int

    instance = M(f=1, oid=ODMObjectId())

    assert isinstance(instance.model_dump_doc()["oid"], ObjectId)


def test_extra_field_document_parsing():
    class M(Model):
        model_config = {"extra": "allow"}

        f: int

    instance = M.model_validate_doc({"_id": ObjectId(), "f": 1, "extra": "hello"})

    assert "extra" in instance.model_dump_doc()


class EmForGenericDefinitionTest(EmbeddedModel):
    f: int


@pytest.mark.skipif(
    sys.version_info[:3] < (3, 9, 0),
    reason="Standard collection generics not supported by python < 3.9",
)
@pytest.mark.parametrize(
    "get_type, value",
    [
        (lambda: list[int], [1, 2, 3]),
        (lambda: dict[str, int], {"a": 1, "b": 2}),
        (lambda: set[int], {1, 2, 3}),
        (lambda: tuple[int, ...], (1, 2, 3)),
        (
            lambda: list[EmForGenericDefinitionTest],
            [EmForGenericDefinitionTest(f=1), EmForGenericDefinitionTest(f=2)],
        ),
        (
            lambda: dict[str, EmForGenericDefinitionTest],
            {
                "a": EmForGenericDefinitionTest(f=1),
                "b": EmForGenericDefinitionTest(f=2),
            },
        ),
        (
            lambda: tuple[EmForGenericDefinitionTest, ...],
            (EmForGenericDefinitionTest(f=1), EmForGenericDefinitionTest(f=2)),
        ),
    ],
)
def test_model_definition_with_new_generics(get_type: Callable, value: Any):
    class M(Model):
        f: get_type()  # type: ignore # 3.9 + syntax

    assert M(f=value).f == value


def test_model_definition_with_literal():
    class M(Model):
        f: Literal["a", "b", "c"]  # noqa: F821

    assert M(f="a").f == "a"


def test_model_definition_with_literal_fail():
    class M(Model):
        f: Literal["a", "b", "c"]  # noqa: F821

    with pytest.raises(ValidationError):
        M(f="w")


def test_model_definition_with_generic_literals():
    class M(Model):
        f: List[Literal["a", "b", "c"]]  # noqa: F821

    assert M(f=["a", "c"]).f == ["a", "c"]


def test_model_with_multiple_optional_fields():
    class Person(Model):
        hashed_password: Optional[str]
        totp_secret: Optional[str] = Field(default=None)
        totp_counter: Optional[int] = Field(default=None)

    user = {
        "hashed_password": "hashed_password",
    }
    Person(**user)
