import pytest

from odmantic.field import Field
from odmantic.model import Model
from odmantic.reference import Reference


def test_build_query_filter_across_reference():
    class Referenced(Model):
        a: int

    class M(Model):
        ref: Referenced = Reference()

    with pytest.raises(
        NotImplementedError, match="filtering across references is not supported"
    ):
        M.ref.a == 12


def test_build_query_filter_across_reference_no_attribute():
    class Referenced(Model):
        a: int

    class M(Model):
        ref: Referenced = Reference()

    with pytest.raises(AttributeError):
        M.ref.does_not_exist  # type: ignore


def test_reference_with_custom_primary_field():
    class Referenced(Model):
        key: int = Field(primary_field=True)

    class M(Model):
        ref: Referenced = Reference()

    r = Referenced(key=1)
    m = M(ref=r)
    assert m.model_dump_doc()["ref"] == 1
