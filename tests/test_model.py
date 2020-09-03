from typing import Any, Callable

import pytest
from pydantic import Field as PDField
from pydantic.main import BaseModel

from odmantic.fields import Field
from odmantic.model import Model


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


@pytest.mark.parametrize("method", (repr, str))
def test_repr_model(method):
    class M(Model):
        a: int

    instance = M(a=5)
    assert method(instance) in [
        f"M(id={repr(instance.id)}, a=5)",
        f"M(a=5, id={repr(instance.id)})",
    ]
