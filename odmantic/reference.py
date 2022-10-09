from enum import Enum
from typing import Any, Generic, Optional, Type, TypeVar

from pydantic.fields import Undefined

from odmantic.typing import Annotated

ModelType = TypeVar("ModelType")


class ODMReferenceInfo:
    """Extra data for an ODM reference."""

    __slots__ = ("key_name",)

    def __init__(self, key_name: Optional[str]):
        self.key_name = key_name


class ReferenceMode(Enum):
    EAGER = "EAGER"
    LAZY = "LAZY"
    QUERY = "QUERY"


EagerReference = Annotated[ModelType, ReferenceMode.EAGER]
LazyReference = Annotated[ModelType, ReferenceMode.LAZY]
Reference = Annotated[ModelType, ReferenceMode.QUERY]


class ReferenceProxy(
    Generic[ModelType],
):
    __instance__: Optional[ModelType] = None
    __pointer__: Any
    """Used to define reference fields.

    Args:
        key_name: optional name of the Mongo key that stores the foreign key

    <!--
    #noqa: DAR201
    -->
    """

    def __init__(self, *, key_name: Optional[str] = None) -> None:
        self.__reference_key_name__ = key_name

    def __resolve__(self, instance: ModelType) -> None:
        self.__instance__ = instance

    def __getattribute__(self, __name: str) -> Any:
        if self.__instance__ is None:
            raise AttributeError(
                "Cannot access attribute of a LazyReference before instance resolution"
            )
        instance_attr = getattr(self.instance, __name, Undefined)
        if instance_attr is not Undefined:
            return instance_attr
        return super().__getattribute__(__name)
