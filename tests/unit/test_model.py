from typing import Any

import pytest
from bson.objectid import ObjectId
from pydantic import Field as PDField

from odmantic.fields import Field
from odmantic.model import Model
from odmantic.reference import Reference
from tests.zoo.person import PersonModel


class TheClassName(Model):
    ...


class TheClassNameModel(Model):
    ...


class TheClassNameOverriden(Model):
    __collection__ = "collection_name"


def test_auto_collection_name():

    assert TheClassName.__collection__ == "the_class_name"

    assert TheClassNameModel.__collection__ == "the_class_name"

    assert TheClassNameOverriden.__collection__ == "collection_name"


def test_auto_collection_name_nested():
    class theNestedClassName(Model):
        ...

    assert theNestedClassName.__collection__ == "the_nested_class_name"

    class TheNestedClassNameOverriden(Model):
        __collection__ = "collection_name"

    assert TheNestedClassNameOverriden.__collection__ == "collection_name"


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
    with pytest.raises(TypeError):

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


@pytest.mark.skip("Not implemented")
def test_overload_id_field():
    class M(Model):
        id: str

    instance = M(id="hello world")
    assert instance.id == "hello world"


@pytest.mark.skip("Not implemented")
def test_overload_id_with_another_primary_key():
    with pytest.raises(TypeError):

        class M(Model):
            id: int
            number: int = Field(primary_key=True)


def test_repr_model():
    class M(Model):
        a: int

    instance = M(a=5)
    assert repr(instance) == f"M(id={repr(instance.id)}, a=5)"


def test_fields_modified_no_modification():
    class M(Model):
        f: int

    instance = M(f=0)
    assert instance.__fields_modified__ == set(["f", "id"])


def test_fields_modified_with_default():
    class M(Model):
        f: int = 5

    instance = M(f=0)
    assert instance.__fields_modified__ == set(["f", "id"])


def test_fields_modified_one_update():
    class M(Model):
        f: int

    instance = M(f=0)
    instance.f = 1
    assert instance.__fields_modified__ == set(["f", "id"])


def test_validate_does_not_copy():
    instance = PersonModel(first_name="Jean", last_name="Pierre")
    assert PersonModel.validate(instance) is instance


def test_validate_from_dict():
    instance = PersonModel.validate({"first_name": "Jean", "last_name": "Pierre"})
    assert isinstance(instance, PersonModel)
    assert instance.first_name == "Jean" and instance.last_name == "Pierre"


def test_fields_modified_on_construction():
    instance = PersonModel(first_name="Jean", last_name="Pierre")
    assert instance.__fields_modified__ == set(["first_name", "last_name", "id"])


def test_fields_modified_on_document_parsing():
    instance = PersonModel.parse_doc(
        {"_id": ObjectId(), "first_name": "Jackie", "last_name": "Chan"}
    )
    assert instance.__fields_modified__ == set(["first_name", "last_name", "id"])


def test_fields_modified_on_object_parsing():
    instance = PersonModel.parse_obj(
        {"_id": ObjectId(), "first_name": "Jackie", "last_name": "Chan"}
    )
    assert instance.__fields_modified__ == set(["first_name", "last_name", "id"])
