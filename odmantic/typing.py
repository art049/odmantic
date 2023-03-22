import sys
from typing import Any
from typing import Callable as TypingCallable
from typing import Tuple, Type, TypeVar, Union

NoArgAnyCallable = TypingCallable[[], Any]

# Handles globally the typing imports from typing or the typing_extensions backport
if sys.version_info < (3, 8):
    from typing_extensions import Literal, get_args, get_origin
else:
    from typing import Literal, get_args, get_origin  # noqa: F401

if sys.version_info < (3, 11):
    from typing_extensions import dataclass_transform
else:
    # FIXME: add this back to coverage once 3.11 is released
    from typing import dataclass_transform  # noqa: F401 # pragma: no cover


# Taken from https://github.com/pydantic/pydantic/pull/2392
# Reimplemented here to avoid a dependency deprecation on pydantic1.7
def lenient_issubclass(
    cls: Any, class_or_tuple: Union[Type[Any], Tuple[Type[Any], ...]]
) -> bool:
    try:
        return isinstance(cls, type) and issubclass(cls, class_or_tuple)
    except TypeError:
        if hasattr(cls, "__origin__"):
            return False
        raise  # pragma: no cover


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
