from typing import TYPE_CHECKING, Any, Optional, Type

from odmantic.fields import ODMBaseField

if TYPE_CHECKING:
    from odmantic.model import Model  # noqa: F401


def Reference(*, key_name: str = None) -> Any:
    return ODMReferenceInfo(key_name=key_name)


class ODMReferenceInfo:
    """Extra data for an ODM reference"""

    __slots__ = ("key_name",)

    def __init__(self, key_name: Optional[str]):
        self.key_name = key_name


class ODMReference(ODMBaseField):

    __slots__ = ("model",)

    def __init__(self, key_name: str, model: Type["Model"]):
        super().__init__(key_name)
        self.model = model
