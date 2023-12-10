import sys
from typing import TYPE_CHECKING, AbstractSet, Any
from typing import Callable as TypingCallable
from typing import (
    ClassVar,
    Dict,
    ForwardRef,
    Iterable,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    _eval_type,
)

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    NoArgAnyCallable: TypeAlias = TypingCallable[[], Any]
    ReprArgs: TypeAlias = "Iterable[tuple[str | None, Any]]"
    AbstractSetIntStr: TypeAlias = "AbstractSet[int] | AbstractSet[str]"
    MappingIntStrAny: TypeAlias = "Mapping[int, Any] | Mapping[str, Any]"
    DictStrAny: TypeAlias = Dict[str, Any]
    IncEx: TypeAlias = "set[int] | set[str] | dict[int, Any] | dict[str, Any] | None"


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

HAS_GENERIC_ALIAS_BUILTIN = sys.version_info[:3] >= (3, 9, 0)  # PEP 560
if HAS_GENERIC_ALIAS_BUILTIN:
    from typing import GenericAlias  # type: ignore
else:
    from typing import _GenericAlias as GenericAlias  # type: ignore # noqa: F401


# Taken from https://github.com/pydantic/pydantic/pull/2392
# Reimplemented here to avoid a dependency deprecation on pydantic1.7
def lenient_issubclass(
    cls: Any, class_or_tuple: Union[Type[Any], Tuple[Type[Any], ...]]
) -> bool:
    try:
        return isinstance(cls, type) and issubclass(cls, class_or_tuple)
    except TypeError:
        if get_origin(cls) is not None or isinstance(cls, GenericAlias):
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


def _check_classvar(v: Optional[Type[Any]]) -> bool:
    if v is None:
        return False

    return v.__class__ == ClassVar.__class__ and getattr(v, "_name", None) == "ClassVar"


# Taken from pydantic v1
def is_classvar(ann_type: Type[Any]) -> bool:
    if _check_classvar(ann_type) or _check_classvar(get_origin(ann_type)):
        return True

    # this is an ugly workaround for class vars that contain forward references and are therefore themselves
    # forward references, see #3679
    if ann_type.__class__ == ForwardRef and ann_type.__forward_arg__.startswith(
        "ClassVar["
    ):
        return True

    return False


def resolve_annotations(
    raw_annotations: Dict[str, Type[Any]], module_name: Optional[str]
) -> Dict[str, Type[Any]]:
    """
    Taken from pydantic v1

    Resolve string or ForwardRef annotations into type objects if possible.
    """
    base_globals: Optional[Dict[str, Any]] = None
    if module_name:
        try:
            module = sys.modules[module_name]
        except KeyError:
            # happens occasionally, see https://github.com/pydantic/pydantic/issues/2363
            pass
        else:
            base_globals = module.__dict__

    annotations = {}
    for name, value in raw_annotations.items():
        if isinstance(value, str):
            if (3, 10) > sys.version_info >= (3, 9, 8) or sys.version_info >= (
                3,
                10,
                1,
            ):
                value = ForwardRef(value, is_argument=False, is_class=True)
            else:
                value = ForwardRef(value, is_argument=False)
        try:
            value = _eval_type(value, base_globals, None)
        except NameError:
            # this is ok, it can be fixed with update_forward_refs
            pass
        annotations[name] = value
    return annotations
