import pytest

from odmantic.field import Field
from odmantic.model import EmbeddedModel, Model
from odmantic.reference import Reference


def test_field_defined_as_primary_key_and_custom_name():
    with pytest.raises(
        ValueError, match="cannot specify a primary field with a custom key_name"
    ):
        Field(primary_field=True, key_name="not _id")


def test_field_defined_as_primary_key_default_name():
    f = Field(primary_field=True)
    assert f.key_name == "_id"


def test_field_define_key_as__id_without_setting_as_primary():
    with pytest.raises(
        ValueError,
        match="cannot specify key_name='_id' without defining the field as primary",
    ):
        Field(key_name="_id")


def test_pos_key_name():
    class M(Model):
        field: int = Field(key_name="alternate_name")

    assert +M.field == "alternate_name"
    assert ++M.field == "$alternate_name"


def test_unknown_attr_embedded_model():
    class E(EmbeddedModel):
        ...

    class M(Model):
        field: E

    with pytest.raises(AttributeError, match="attribute unknown_attr not found in E"):
        M.field.unknown_attr  # type: ignore


@pytest.mark.parametrize("operator_name", ("lt", "lte", "gt", "gte", "match"))
def test_reference_field_operator_not_allowed(operator_name: str):
    class E(Model):
        ...

    class M(Model):
        field: E = Reference()

    with pytest.raises(
        AttributeError,
        match=f"operator {operator_name} not allowed for ODMReference fields",
    ):
        getattr(M.field, operator_name)
