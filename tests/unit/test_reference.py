import pytest

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
