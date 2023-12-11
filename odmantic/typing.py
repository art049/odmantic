import sys
from typing import TYPE_CHECKING, AbstractSet, Any  # noqa: F401
from typing import Callable as TypingCallable
from typing import Dict, Iterable, Mapping, Tuple, Type, TypeVar, Union  # noqa: F401

from pydantic.v1.typing import is_classvar, resolve_annotations  # noqa: F401
from pydantic.v1.utils import lenient_issubclass

if sys.version_info < (3, 11):
    from typing_extensions import dataclass_transform
else:
    from typing import dataclass_transform  # noqa: F401

if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

if sys.version_info < (3, 9):
    from typing import _GenericAlias as GenericAlias  # noqa: F401

    # Even if get_args and get_origin are available in typing, it's important to
    # import them from typing_extensions to have proper origins with Annotated fields
    from typing_extensions import Annotated, get_args, get_origin
else:
    from typing import GenericAlias  # type: ignore  # noqa: F401
    from typing import Annotated, get_args, get_origin  # noqa: F401


if TYPE_CHECKING:
    NoArgAnyCallable: TypeAlias = TypingCallable[[], Any]
    ReprArgs: TypeAlias = "Iterable[tuple[str | None, Any]]"
    AbstractSetIntStr: TypeAlias = "AbstractSet[int] | AbstractSet[str]"
    MappingIntStrAny: TypeAlias = "Mapping[int, Any] | Mapping[str, Any]"
    DictStrAny: TypeAlias = Dict[str, Any]
    IncEx: TypeAlias = "set[int] | set[str] | dict[int, Any] | dict[str, Any] | None"


def is_type_argument_subclass(
    type_: Type, class_or_tuple: Union[Type[Any], Tuple[Type[Any], ...]]
) -> bool:
    args = get_args(type_)
    return any(lenient_issubclass(arg, class_or_tuple) for arg in args)


T = TypeVar("T")


def get_first_type_argument_subclassing(
    type_: Type, cls: Type[T]
) -> Union[Type[T], None]:
    args: Tuple[Type, ...] = get_args(type_)
    for arg in args:
        if lenient_issubclass(arg, cls):
            return arg
    return None
