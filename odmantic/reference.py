from typing import Any, Optional


def Reference(*, key_name: Optional[str] = None) -> Any:
    return ODMReferenceInfo(key_name=key_name)


class ODMReferenceInfo:
    """Extra data for an ODM reference."""

    __slots__ = ("key_name",)

    def __init__(self, key_name: Optional[str]):
        self.key_name = key_name
