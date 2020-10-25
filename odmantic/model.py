import datetime
import decimal
import enum
import pathlib
import re
import sys
import uuid
from abc import ABCMeta
from collections.abc import Callable as abcCallable
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    no_type_check,
)

import bson
import pydantic
from pydantic.error_wrappers import ValidationError
from pydantic.fields import Field as PDField
from pydantic.fields import FieldInfo as PDFieldInfo
from pydantic.fields import Undefined
from pydantic.tools import parse_obj_as
from pydantic.typing import is_classvar, resolve_annotations
from pydantic.utils import lenient_issubclass

from odmantic.bson import (
    _BSON_SUBSTITUTED_FIELDS,
    BSON_TYPES_ENCODERS,
    BaseBSONModel,
    ObjectId,
    _decimalDecimal,
)
from odmantic.field import (
    FieldProxy,
    ODMBaseField,
    ODMEmbedded,
    ODMField,
    ODMFieldInfo,
    ODMReference,
)
from odmantic.reference import ODMReferenceInfo

if TYPE_CHECKING:

    from pydantic.typing import (
        AbstractSetIntStr,
        DictStrAny,
        MappingIntStrAny,
        ReprArgs,
    )

USES_OLD_TYPING_INTERFACE = sys.version_info[:3] < (3, 7, 0)  # PEP 560
if USES_OLD_TYPING_INTERFACE:
    from typing import _subs_tree  # type: ignore  # noqa


UNTOUCHED_TYPES = FunctionType, property, classmethod, staticmethod


def should_touch_field(value: Any = None, type_: Optional[Type] = None) -> bool:
    return not (
        lenient_issubclass(type_, UNTOUCHED_TYPES)
        or isinstance(value, UNTOUCHED_TYPES)
        or (type_ is not None and is_classvar(type_))
    )


def is_valid_odm_field_name(name: str) -> bool:
    return not name.startswith("__") and not name.endswith("__")


def raise_on_invalid_key_name(name: str) -> None:
    # https://docs.mongodb.com/manual/reference/limits/#Restrictions-on-Field-Names
    if name.startswith("$"):
        raise TypeError("key_name cannot start with the dollar sign ($) character")
    if "." in name:
        raise TypeError("key_name cannot contain the dot (.) character")


def to_snake_case(s: str) -> str:
    tmp = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", tmp).lower()


def find_duplicate_key(fields: Iterable[ODMBaseField]) -> Optional[str]:
    seen: Set[str] = set()
    for f in fields:
        if f.key_name in seen:
            return f.key_name
        seen.add(f.key_name)
    return None


_IMMUTABLE_TYPES = (
    type(None),
    bool,
    int,
    float,
    str,
    bytes,
    tuple,
    frozenset,
    datetime.date,
    datetime.time,
    datetime.datetime,
    datetime.timedelta,
    enum.Enum,
    decimal.Decimal,
    pathlib.Path,
    uuid.UUID,
    pydantic.BaseModel,
    bson.ObjectId,
    bson.Decimal128,
    _decimalDecimal,
)


def is_type_mutable(type_: Type) -> bool:
    type_origin: Optional[Type] = getattr(type_, "__origin__", None)
    if type_origin is not None:
        type_args: Tuple[Type, ...] = getattr(type_, "__args__", ())
        for type_arg in type_args:
            if type_arg is ...:  # Handle tuple definition
                continue
            if lenient_issubclass(type_origin, Iterable) and lenient_issubclass(
                type_arg, EmbeddedModel
            ):  # Handle nested embedded models
                return True
            if is_type_mutable(type_arg):
                return True
        if type_origin is Union:
            return False
        return not lenient_issubclass(type_origin, _IMMUTABLE_TYPES)
    else:
        return not (
            type_ is None or lenient_issubclass(type_, _IMMUTABLE_TYPES)  # type:ignore
        )


def is_type_forbidden(t: Type) -> bool:
    if t is Callable or t is abcCallable:
        # Callable type require a special treatment since typing.Callable is not a class
        return True
    return False


def validate_type(type_: Type) -> Type:
    if not should_touch_field(type_=type_) or lenient_issubclass(
        type_, (Model, EmbeddedModel)
    ):
        return type_
    if is_type_forbidden(type_):
        raise TypeError(f"{type_} fields are not supported")

    subst_type = _BSON_SUBSTITUTED_FIELDS.get(type_)
    if subst_type is not None:
        return subst_type

    # Typing replacement
    # 3.7+:
    # https://github.com/python/cpython/blob/e022bbc169ca1428dc3017187012de17ce6e0bc7/Lib/typing.py#L605
    # 3.6:
    # https://github.com/python/cpython/blob/aed26482c7baab078f39d5cd52216fb8ee9f276f/Lib/typing.py#L570
    type_origin: Optional[Type] = getattr(type_, "__origin__", None)
    if type_origin is not None:
        type_args: Tuple[Type, ...] = getattr(type_, "__args__", ())
        new_arg_types = tuple(validate_type(subtype) for subtype in type_args)
        setattr(type_, "__args__", new_arg_types)
        if USES_OLD_TYPING_INTERFACE:
            # FIXME: there is probably a more elegant way of doing this
            subs_tree = type_._subs_tree()
            if type_origin is Union:
                tree_hash = hash(
                    frozenset(subs_tree) if isinstance(subs_tree, tuple) else subs_tree
                )
            else:
                tree_hash = hash(
                    subs_tree if isinstance(subs_tree, tuple) else frozenset(subs_tree)
                )
            setattr(type_, "__tree_hash__", tree_hash)
    return type_


class BaseModelMetaclass(pydantic.main.ModelMetaclass):
    @staticmethod
    def __validate_cls_namespace__(name: str, namespace: Dict) -> None:  # noqa C901
        """Validate the class name space in place"""
        annotations = resolve_annotations(
            namespace.get("__annotations__", {}), namespace.get("__module__")
        )
        odm_fields: Dict[str, ODMBaseField] = {}
        references: List[str] = []
        bson_serialized_fields: Set[str] = set()
        mutable_fields: Set[str] = set()

        # Make sure all fields are defined with type annotation
        for field_name, value in namespace.items():
            if (
                should_touch_field(value=value)
                and is_valid_odm_field_name(field_name)
                and field_name not in annotations
            ):
                raise TypeError(
                    f"field {field_name} is defined without type annotation"
                )

        # Validate fields types and substitute bson fields
        for (field_name, field_type) in annotations.items():
            if is_valid_odm_field_name(field_name) and should_touch_field(
                type_=field_type
            ):
                substituted_type = validate_type(field_type)
                # Handle BSON serialized fields after substitution to allow some
                # builtin substitution
                bson_serialization_method = getattr(substituted_type, "__bson__", None)
                if bson_serialization_method is not None:
                    bson_serialized_fields.add(field_name)
                annotations[field_name] = substituted_type

        # Validate fields
        for (field_name, field_type) in annotations.items():
            value = namespace.get(field_name, Undefined)

            if not is_valid_odm_field_name(field_name) or not should_touch_field(
                value, field_type
            ):
                continue  # pragma: no cover
                # https://github.com/nedbat/coveragepy/issues/198

            if isinstance(value, PDFieldInfo):
                raise TypeError("please use odmantic.Field instead of pydantic.Field")

            if lenient_issubclass(field_type, EmbeddedModel):
                if isinstance(value, ODMFieldInfo):
                    namespace[field_name] = value.pydantic_field_info
                    key_name = (
                        value.key_name if value.key_name is not None else field_name
                    )
                    primary_field = value.primary_field
                else:
                    key_name = field_name
                    primary_field = False

                odm_fields[field_name] = ODMEmbedded(
                    primary_field=primary_field, model=field_type, key_name=key_name
                )
            elif lenient_issubclass(field_type, Model):
                if not isinstance(value, ODMReferenceInfo):
                    raise TypeError(
                        "cannot define a reference {field_name} (in {name}) without"
                        " a Reference assigned to it"
                    )
                key_name = value.key_name if value.key_name is not None else field_name
                raise_on_invalid_key_name(key_name)
                odm_fields[field_name] = ODMReference(
                    model=field_type, key_name=key_name
                )
                references.append(field_name)
                del namespace[field_name]  # Remove default ODMReferenceInfo value
            else:
                if is_type_mutable(field_type):
                    mutable_fields.add(field_name)
                if isinstance(value, ODMFieldInfo):
                    key_name = (
                        value.key_name if value.key_name is not None else field_name
                    )
                    raise_on_invalid_key_name(key_name)
                    odm_fields[field_name] = ODMField(
                        primary_field=value.primary_field, key_name=key_name
                    )
                    namespace[field_name] = value.pydantic_field_info

                elif value is Undefined:
                    odm_fields[field_name] = ODMField(
                        primary_field=False, key_name=field_name
                    )

                else:
                    try:
                        parse_obj_as(field_type, value)
                    except ValidationError:
                        raise TypeError(
                            f"Unhandled field definition {name}: {repr(field_type)}"
                            f" = {repr(value)}"
                        )
                    odm_fields[field_name] = ODMField(
                        primary_field=False, key_name=field_name
                    )

        duplicate_key = find_duplicate_key(odm_fields.values())
        if duplicate_key is not None:
            raise TypeError(f"Duplicated key_name: {duplicate_key} in {name}")
        # NOTE: Duplicate key detection make sur that at most one primary key is
        # defined
        namespace["__annotations__"] = annotations
        namespace["__odm_fields__"] = odm_fields
        namespace["__references__"] = tuple(references)
        namespace["__bson_serialized_fields__"] = frozenset(bson_serialized_fields)
        namespace["__mutable_fields__"] = frozenset(mutable_fields)

    @no_type_check
    def __new__(
        mcs,
        name: str,
        bases: Tuple[type, ...],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ):
        is_custom_cls = namespace.get(
            "__module__"
        ) != "odmantic.model" and namespace.get("__qualname__") not in (
            "_BaseODMModel",
            "Model",
            "EmbeddedModel",
        )
        if is_custom_cls:
            # Handle calls from pydantic.main.create_model (used internally by FastAPI)
            patched_bases = []
            for b in bases:
                if hasattr(b, "__pydantic_model__"):
                    patched_bases.append(b.__pydantic_model__)
                else:
                    patched_bases.append(b)
            bases = tuple(patched_bases)
            # Nullify unset docstring (to avoid getting the docstrings from the parent
            # classes)
            if namespace.get("__doc__", None) is None:
                namespace["__doc__"] = ""

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if is_custom_cls:
            # Patch Model related fields to build a "pure" pydantic model
            odm_fields: Dict[str, ODMBaseField] = namespace["__odm_fields__"]
            for field_name, field in odm_fields.items():
                if isinstance(field, (ODMReference, ODMEmbedded)):
                    namespace["__annotations__"][
                        field_name
                    ] = field.model.__pydantic_model__
            # Build the pydantic model
            pydantic_cls = pydantic.main.ModelMetaclass.__new__(
                mcs, f"{name}.__pydantic_model__", (BaseBSONModel,), namespace, **kwargs
            )
            # Change the title to generate clean JSON schemas from this "pure" model
            pydantic_cls.__config__.title = name

            cls.__pydantic_model__ = pydantic_cls
            for name, field in cls.__odm_fields__.items():
                setattr(cls, name, FieldProxy(parent=None, field=field))

        return cls


class ModelMetaclass(BaseModelMetaclass):
    @no_type_check
    def __new__(  # noqa C901
        mcs,
        name: str,
        bases: Tuple[type, ...],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ):
        if namespace.get("__module__") != "odmantic.model" and namespace.get(
            "__qualname__"
        ) not in ("_BaseODMModel", "Model"):
            mcs.__validate_cls_namespace__(name, namespace)
            primary_field: Optional[str] = None
            odm_fields: Dict[str, ODMBaseField] = namespace["__odm_fields__"]

            for field_name, field in odm_fields.items():
                if isinstance(field, ODMField) and field.primary_field:
                    primary_field = field_name
                    break

            if primary_field is None:
                if "id" in odm_fields:
                    raise TypeError(
                        "can't automatically generate a primary field since an 'id' "
                        "field already exists"
                    )
                primary_field = "id"
                odm_fields["id"] = ODMField(primary_field=True, key_name="_id")
                namespace["id"] = PDField(default_factory=ObjectId)
                namespace["__annotations__"]["id"] = ObjectId

            namespace["__primary_field__"] = primary_field

            if "__collection__" in namespace:
                collection_name = namespace["__collection__"]
            else:
                cls_name = name
                if cls_name.endswith("Model"):
                    # TODO document this
                    cls_name = cls_name[:-5]  # Strip Model in the class name
                collection_name = to_snake_case(cls_name)
                namespace["__collection__"] = collection_name

            # Validate the collection name
            # https://docs.mongodb.com/manual/reference/limits/#Restriction-on-Collection-Names
            if "$" in collection_name:
                raise TypeError(
                    f"Invalid collection name for {name}: cannot contain '$'"
                )
            if collection_name == "":
                raise TypeError(f"Invalid collection name for {name}: cannot be empty")
            if collection_name.startswith("system."):
                raise TypeError(
                    f"Invalid collection name for {name}:"
                    " cannot start with 'system.'"
                )

        return super().__new__(mcs, name, bases, namespace, **kwargs)

    def __pos__(cls) -> str:
        return cast(str, getattr(cls, "__collection__"))


class EmbeddedModelMetaclass(BaseModelMetaclass):
    @no_type_check
    def __new__(
        mcs,
        name: str,
        bases: Tuple[type, ...],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ):

        if namespace.get("__module__") != "odmantic.model" and namespace.get(
            "__qualname__"
        ) not in ("_BaseODMModel", "EmbeddedModel"):
            mcs.__validate_cls_namespace__(name, namespace)
            odm_fields: Dict[str, ODMBaseField] = namespace["__odm_fields__"]
            for field in odm_fields.values():
                if isinstance(field, ODMField) and field.primary_field:
                    raise TypeError(
                        f"cannot define a primary field in {name} embedded document"
                    )

        return super().__new__(mcs, name, bases, namespace, **kwargs)


TBase = TypeVar("TBase", bound="_BaseODMModel")


class _BaseODMModel(pydantic.BaseModel, metaclass=ABCMeta):
    """Base class for [Model][odmantic.model.Model] and
    [EmbeddedModel][odmantic.model.EmbeddedModel].

    !!! warning
        This internal class should never be instanciated directly.
    """

    if TYPE_CHECKING:
        __odm_fields__: ClassVar[Dict[str, ODMBaseField]] = {}
        __bson_serialized_fields__: ClassVar[FrozenSet[str]] = frozenset()
        __mutable_fields__: ClassVar[FrozenSet[str]] = frozenset()
        __references__: ClassVar[Tuple[str, ...]] = ()
        __pydantic_model__: ClassVar[Type[BaseBSONModel]]
        __fields_modified__: Set[str] = set()

    __slots__ = ("__fields_modified__",)

    class Config:
        validate_all = True
        validate_assignment = True
        json_encoders = BSON_TYPES_ENCODERS

    @classmethod
    def validate(cls: Type[TBase], value: Any) -> TBase:
        if isinstance(value, cls):
            # Do not copy the object as done in pydantic
            # This enable to keep the same python object
            return value
        return super().validate(value)

    def __repr_args__(self) -> "ReprArgs":
        # Place the id field first in the repr string
        args = list(super().__repr_args__())
        id_arg = next((arg for arg in args if arg[0] == "id"), None)
        if id_arg is None:
            return args
        args.remove(id_arg)
        args = [id_arg] + args
        return args

    def copy(
        self: TBase,
        *,
        include: Union[None, "AbstractSetIntStr", "MappingIntStrAny"] = None,
        exclude: Union[None, "AbstractSetIntStr", "MappingIntStrAny"] = None,
        update: Optional["DictStrAny"] = None,
        deep: bool = False,
    ) -> TBase:
        """WARNING: Not Implemented"""
        # TODO implement
        raise NotImplementedError

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        self.__fields_modified__.add(name)

    def doc(self, include: Optional["AbstractSetIntStr"] = None) -> Dict[str, Any]:
        """Generate a document representation of the instance (as a dictionary).

        Args:
            include: field that should be included; if None, all the field will be
                included

        Returns:
            the document associated to the instance
        """
        raw_doc = self.dict()
        doc: Dict[str, Any] = {}
        for field_name, field in self.__odm_fields__.items():
            if include is not None and field_name not in include:
                continue
            if isinstance(field, ODMReference):
                doc[field.key_name] = raw_doc[field_name]["id"]
            else:
                if field_name in self.__bson_serialized_fields__:
                    doc[field.key_name] = self.__fields__[field_name].type_.__bson__(
                        raw_doc[field_name]
                    )
                else:
                    doc[field.key_name] = raw_doc[field_name]
        return doc

    @classmethod
    def parse_doc(cls: Type[TBase], raw_doc: Dict) -> TBase:
        """Parse a BSON document into an instance of the Model

        Args:
            raw_doc: document to parse (as Dict)

        Returns:
            an instance of the Model class this method is called on.
        """
        doc: Dict[str, Any] = {}
        for field_name, field in cls.__odm_fields__.items():
            if isinstance(field, ODMReference):
                doc[field_name] = field.model.parse_doc(raw_doc[field.key_name])
            else:
                doc[field_name] = raw_doc[field.key_name]
        instance = cls.parse_obj(doc)
        return instance


class Model(_BaseODMModel, metaclass=ModelMetaclass):
    """Class that can be extended to create an ODMantic Model.

    Each model will be bound to a MongoDB collection. You can customize the collection
    name by setting the `__collection__` class variable in the model classes.
    """

    if TYPE_CHECKING:
        __collection__: ClassVar[str] = ""
        __primary_field__: ClassVar[str] = ""

        id: Union[ObjectId, Any]  # TODO fix basic id field typing

    def __init__(__odmantic_self__, **data: Any):
        super().__init__(**data)
        # Uses something other than `self` the first arg to allow "self" as a settable
        # attribute
        object.__setattr__(
            __odmantic_self__,
            "__fields_modified__",
            set(__odmantic_self__.__odm_fields__.keys()),
        )

    def __setattr__(self, name: str, value: Any) -> None:
        if name == self.__primary_field__:
            # TODO implement
            raise NotImplementedError(
                "Reassigning a new primary key is not supported yet"
            )
        super().__setattr__(name, value)


class EmbeddedModel(_BaseODMModel, metaclass=EmbeddedModelMetaclass):
    """Class that can be extended to create an ODMantic Embedded Model.

    An embedded document cannot be persisted directly to the database but should be
    integrated in a regular ODMantic Model.
    """
