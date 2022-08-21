from types import FunctionType
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union,
)

import pytest
from bson import ObjectId
from bson.decimal128 import Decimal128
from bson.regex import Regex
from pydantic import Field as PDField
from pydantic.error_wrappers import ValidationError

from odmantic.field import Field
from odmantic.model import EmbeddedModel, Model
from odmantic.reference import Reference


class TheClassName(Model):
    ...


class TheClassNameModel(Model):
    ...


class TheClassNameOverriden(Model):
    class Config:
        collection = "collection_name"


def test_auto_collection_name():

    assert TheClassName.__collection__ == "the_class_name"

    assert TheClassNameModel.__collection__ == "the_class_name"

    assert TheClassNameOverriden.__collection__ == "collection_name"


def test_auto_collection_name_nested():
    class theNestedClassName(Model):
        ...

    assert theNestedClassName.__collection__ == "the_nested_class_name"

    class TheNestedClassNameOverriden(Model):
        class Config:
            collection = "collection_name"

    assert TheNestedClassNameOverriden.__collection__ == "collection_name"


def test_get_collection_name_pos():
    class Thing(Model):
        ...

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


def test_optional_field():
    class M(Model):
        f: Optional[str]

    assert M().f is None
    assert M(f=None).f is None
    assert M(f="hello world").f == "hello world"


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
    assert instance.doc() == {"_id": "Jack"}


def test_weird_overload_id_field():
    class M(Model):
        id: int
        name: str = Field(primary_field=True)

    instance = M(id=15, name="Johnny")
    assert instance.doc() == {"_id": "Johnny", "id": 15}


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


def test_invalid_collection_name_dollar():
    with pytest.raises(TypeError, match=r"cannot contain '\$'"):

        class A(Model):
            class Config:
                collection = "hello$world"


def test_invalid_collection_name_empty():
    with pytest.raises(TypeError, match="cannot be empty"):

        class A(Model):
            class Config:
                collection = ""


def test_invalid_collection_name_contain_system_dot():
    with pytest.raises(TypeError, match="cannot start with 'system.'"):

        class A(Model):
            class Config:
                collection = "system.hi"


def test_legacy_custom_collection_name():
    with pytest.warns(
        DeprecationWarning,
        match="Defining the collection name with `__collection__` is deprecated",
    ):

        class M(Model):
            __collection__ = "collection_name"

    assert M.__collection__ == "collection_name"


def test_embedded_model_key_name():
    class E(EmbeddedModel):
        f: int = 3

    class M(Model):
        field: E = Field(E(), key_name="hello")

    doc = M().doc()
    assert "hello" in doc
    assert doc["hello"] == {"f": 3}


def test_embedded_model_as_primary_field():
    class E(EmbeddedModel):
        f: int

    class M(Model):
        field: E = Field(primary_field=True)

    assert M(field=E(f=1)).doc() == {"_id": {"f": 1}}


def test_untouched_types_function():
    def id_str(self) -> str:  # pragma: no cover
        return str(self.id)

    class M(Model):
        class Config:
            arbitrary_types_allowed = True

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
    assert "cls_var" not in m.doc().keys()


def test_forbidden_config_parameter_validate_all():
    with pytest.raises(ValueError, match="'Config.validate_all' is not supported"):

        class M(Model):
            class Config:
                validate_all = False


def test_forbidden_config_parameter_validate_assignment():
    with pytest.raises(
        ValueError, match="'Config.validate_assignment' is not supported"
    ):

        class M(Model):
            class Config:
                validate_assignment = False


def test_embedded_model_alternate_key_name():
    class Em(EmbeddedModel):
        name: str = Field(key_name="username")

    class M(Model):
        f: Em

    instance = M(f=Em(name="Jack"))
    doc = instance.doc()
    assert doc["f"] == {"username": "Jack"}
