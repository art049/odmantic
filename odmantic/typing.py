import sys
from typing import TYPE_CHECKING, AbstractSet, Any, Optional  # noqa: F401
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


def is_optional(type_: Type) -> bool:
    type_origin: Optional[Type] = getattr(type_, "__origin__", None)
    if type_origin is Union:
        type_args: Tuple[Type, ...] = getattr(type_, "__args__", ())
        if type_args:
            return type_origin is Union and type_args[1] is type(None)
    return False


def resolve_optional_to_some(type_: Type) -> Type:
    if is_optional(type_):
        type_args: Tuple[Type, ...] = getattr(type_, "__args__", ())
        assert type_args
        type_ = type_args[0]
    return type_


def is_type_argument_subclass(
    type_: Type, class_or_tuple: Union[Type[Any], Tuple[Type[Any], ...]]
) -> bool:
    type_ = resolve_optional_to_some(type_)
    args = get_args(type_)
    return any(lenient_issubclass(arg, class_or_tuple) for arg in args)


T = TypeVar("T")


def get_first_type_argument_subclassing(
    type_: Type, cls: Type[T]
) -> Union[Type[T], None]:
    type_ = resolve_optional_to_some(type_)
    args: Tuple[Type, ...] = get_args(type_)
    for arg in args:
        if lenient_issubclass(arg, cls):
            return arg
    return None


def get_generic_origin(type_: Type) -> Optional[Any]:
    type_ = resolve_optional_to_some(type_)
    return get_origin(type_)
