from typing import Type

from odmantic.typing import get_args, get_origin


def are_generics_equal(g1: Type, g2: Type) -> bool:
    """Check if two generic types are equal."""
    if g1 == g2:
        return True
    origin_g1 = get_origin(g1)
    origin_g2 = get_origin(g2)
    if origin_g1 is None or origin_g2 is None or origin_g1 != origin_g2:
        return False
    args_g1 = get_args(g1)
    args_g2 = get_args(g2)
    if len(args_g1) != len(args_g2):
        return False
    return all(are_generics_equal(a1, a2) for a1, a2 in zip(args_g1, args_g2))
