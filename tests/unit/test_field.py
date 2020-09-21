import pytest

from odmantic.field import Field


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
