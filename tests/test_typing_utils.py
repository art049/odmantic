from typing import Dict, List, Set, Tuple

from typing_utils import are_generics_equal


def test_are_generics_equal_two_different_origin():
    assert not are_generics_equal(List[str], Set[str])


def test_are_generics_equal_different_arg_count():
    assert not are_generics_equal(Tuple[str], Tuple[str, str])
    assert not are_generics_equal(Tuple[str], Tuple[str, ...])


def test_are_generics_equal_different_args():
    assert not are_generics_equal(Tuple[str, int], Tuple[int, str])
    assert not are_generics_equal(
        Tuple[str, int, Dict[int, str]], Tuple[str, int, Dict[int, int]]
    )
