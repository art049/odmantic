from typing import Any, Optional


def Reference(*, key_name: Optional[str] = None) -> Any:
    """Used to define reference fields.

    Args:
        key_name: name of the Mongo key that stores the foreign key

    <!--
    #noqa: DAR201
    -->
    """
    return ODMReferenceInfo(key_name=key_name)


class ODMReferenceInfo:
    """Extra data for an ODM reference."""

    __slots__ = ("key_name",)

    def __init__(self, key_name: Optional[str]):
        self.key_name = key_name
