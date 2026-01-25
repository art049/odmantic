import sys
from typing import (  # noqa: F401
    TYPE_CHECKING,
    AbstractSet,
    Any,
    ClassVar,
    Dict,
    ForwardRef,
    Iterable,
    Mapping,
    Tuple,
    Type,
    TypeVar,
    Union,
    _eval_type,  # type: ignore
)
import typing
import types
from typing import Callable as TypingCallable

# Copy from Pydantic: pydantic/v1/typing.py
# This can probably be replaced by the logic in: pydantic/_internal/_typing_extra.py
# after dropping support for Python 3.8 and 3.9
try:
    from typing import GenericAlias as TypingGenericAlias  # type: ignore
except ImportError:
    # python < 3.9 does not have GenericAlias (list[int], tuple[str, ...] and so on)
    TypingGenericAlias = ()
if sys.version_info < (3, 10):

    def is_union(tp: Union[Type[Any], None]) -> bool:
        return tp is Union

    WithArgsTypes = (TypingGenericAlias,)

else:
    import types
    import typing

    def is_union(tp: Union[Type[Any], None]) -> bool:
        return tp is Union or tp is types.UnionType  # noqa: E721

    WithArgsTypes = (typing._GenericAlias, types.GenericAlias, types.UnionType)


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


def lenient_issubclass(
    cls: Any, class_or_tuple: Union[Type[Any], Tuple[Type[Any], ...], None]
) -> bool:
    # Copy of Pydantic: pydantic/_internal/_utils.py
    try:
        return isinstance(cls, type) and issubclass(cls, class_or_tuple)  # type: ignore[arg-type]
    except TypeError:  # pragma: no cover
        if isinstance(cls, WithArgsTypes):
            return False
        raise  # pragma: no cover


def _check_classvar(v: Union[Type[Any], None]) -> bool:
    # Copy of Pydantic: pydantic/v1/typing.py
    # This can probably be replaced by the logic in: pydantic/_internal/_typing_extra.py
    # after dropping support for Python 3.8 and 3.9
    if v is None:
        return False

    return v.__class__ == ClassVar.__class__ and getattr(v, "_name", None) == "ClassVar"


def is_classvar(ann_type: Type[Any]) -> bool:
    # Copy of Pydantic: pydantic/v1/typing.py
    # This can probably be replaced by the logic in: pydantic/_internal/_typing_extra.py
    # after dropping support for Python 3.8 and 3.9
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
    raw_annotations: Dict[str, Type[Any]], module_name: Union[str, None]
) -> Dict[str, Type[Any]]:
    # Ref: pydantic/v1/typing.py
    # Copy from Pydantic v2's pydantic.v1 for compatibility with versions of Python not
    # supported by Pydantic v2, after dropping support for Python 3.8 and 3.9 this can
    # be replaced by the logic used in Pydantic v2's ModelMetaclass.__new__
    # in: pydantic/_internal/_model_construction.py
    base_globals: Union[Dict[str, Any], None] = None
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
            if sys.version_info >= (3, 13):
                value = _eval_type(value, base_globals, None, type_params=())
            else:
                value = _eval_type(value, base_globals, None)
        except NameError:
            # this is ok, it can be fixed with update_forward_refs
            pass
        annotations[name] = value
    return annotations


def get_annotations_from_namespace(class_dict: Dict[str, Any]) -> Dict[str, Any]:
    # Ref: https://github.com/pydantic/pydantic/pull/11991
    raw_annotations: Dict[str, Any] = class_dict.get("__annotations__", {})
    if sys.version_info >= (3, 14) and "__annotations__" not in class_dict:
        from annotationlib import (
            Format,
            call_annotate_function,
            get_annotate_from_class_namespace,
        )

        if annotate := get_annotate_from_class_namespace(class_dict):
            raw_annotations = call_annotate_function(annotate, format=Format.FORWARDREF)
    return raw_annotations


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
