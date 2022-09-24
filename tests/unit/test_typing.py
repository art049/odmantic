from typing import Dict, List, Set

from odmantic.model import EmbeddedModel
from odmantic.typing import get_first_type_argument_subclassing


def test_get_first_type_argument_subclassing():
    class E(EmbeddedModel):
        e: int

    assert get_first_type_argument_subclassing(List[E], EmbeddedModel) == E
    assert get_first_type_argument_subclassing(Set[E], EmbeddedModel) == E
    assert get_first_type_argument_subclassing(Dict[int, E], EmbeddedModel) == E


def test_get_first_type_argument_subclassing_on_non_matching_generics():
    class E(EmbeddedModel):
        e: int

    assert get_first_type_argument_subclassing(E, EmbeddedModel) is None
    assert get_first_type_argument_subclassing(int, EmbeddedModel) is None
    assert get_first_type_argument_subclassing(Dict[int, str], EmbeddedModel) is None
