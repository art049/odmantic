import re
from abc import ABCMeta
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    FrozenSet,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    no_type_check,
)

import pydantic
from pydantic.fields import Field as PDField
from pydantic.fields import FieldInfo as PDFieldInfo
from pydantic.fields import Undefined
from pydantic.types import PyObject
from pydantic.typing import resolve_annotations

from odmantic.fields import ODMBaseField, ODMField, ODMFieldInfo
from odmantic.reference import ODMReference, ODMReferenceInfo

from .types import _SUBSTITUTION_TYPES, BSONSerializedField, _objectId

if TYPE_CHECKING:

    from pydantic.typing import (
        ReprArgs,
        AbstractSetIntStr,
        MappingIntStrAny,
        DictStrAny,
    )

UNTOUCHED_TYPES = FunctionType, property, classmethod, staticmethod


def is_valid_odm_field(name: str) -> bool:
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


def find_duplicate_key(fields: Sequence[ODMField]) -> Optional[str]:
    seen: Set[str] = set()
    for f in fields:
        if f.key_name in seen:
            return f.key_name
        seen.add(f.key_name)
    return None


class BaseModelMetaclass(ABCMeta):
    @no_type_check
    def __new__(cls, name, bases, namespace, **kwargs):  # noqa C901
        if (namespace.get("__module__"), namespace.get("__qualname__")) != (
            "odmantic.model",
            "Model",
        ):
            annotations = resolve_annotations(
                namespace.get("__annotations__", {}), namespace.get("__module__")
            )
            odm_fields: Dict[str, ODMBaseField] = {}
            references: List[str] = []
            bson_serialized_fields: Set[str] = set()

            # TODO handle class vars
            # Substitute bson types
            for k, v in annotations.items():
                subst_type = _SUBSTITUTION_TYPES.get(v)
                if subst_type is not None:
                    print(f"Subst: {v} -> {subst_type}")
                    annotations[k] = subst_type
            namespace["__annotations__"] = annotations
            for (field_name, field_type) in annotations.items():
                if not is_valid_odm_field(field_name) or (
                    isinstance(field_type, UNTOUCHED_TYPES) and field_type != PyObject
                ):
                    continue
                if BSONSerializedField in getattr(field_type, "__bases__", ()):
                    bson_serialized_fields.add(field_name)
                value = namespace.get(field_name, Undefined)
                if isinstance(value, ODMFieldInfo):
                    key_name = (
                        value.key_name if value.key_name is not None else field_name
                    )
                    raise_on_invalid_key_name(key_name)
                    odm_fields[field_name] = ODMField(
                        primary_field=value.primary_field, key_name=key_name
                    )
                    namespace[field_name] = value.pydantic_field_info

                elif isinstance(value, ODMReferenceInfo):
                    if not issubclass(field_type, Model):
                        raise TypeError(
                            f"cannot define a reference {field_name} (in {name}) on "
                            "a model not created with odmantic.Model"
                        )
                    key_name = (
                        value.key_name if value.key_name is not None else field_name
                    )
                    raise_on_invalid_key_name(key_name)
                    odm_fields[field_name] = ODMReference(
                        model=field_type, key_name=key_name
                    )
                    references.append(field_name)
                elif value is Undefined:
                    odm_fields[field_name] = ODMField(
                        primary_field=False, key_name=field_name
                    )

                elif value is PDFieldInfo:
                    raise TypeError(
                        "please use odmantic.Field instead of pydantic.Field"
                    )
                elif isinstance(value, field_type):
                    odm_fields[field_name] = ODMField(
                        primary_field=False, key_name=field_name
                    )

                else:
                    raise TypeError(f"Unhandled field definition {name}:{value}")

            for field_name, value in namespace.items():
                # TODO check references defined without type
                # TODO find out what to do with those fields
                if (
                    field_name in annotations
                    or not is_valid_odm_field(field_name)
                    or isinstance(value, UNTOUCHED_TYPES)
                ):
                    continue
                odm_fields[field_name] = ODMField(
                    primary_field=False, key_name=field_name
                )

            duplicate_key = find_duplicate_key(odm_fields.values())
            if duplicate_key is not None:
                raise TypeError(f"Duplicate key_name: {duplicate_key} in {name}")

            namespace["__odm_fields__"] = odm_fields
            namespace["__references__"] = tuple(references)
            namespace["__bson_serialized_fields__"] = frozenset(bson_serialized_fields)

        return cls


class ModelMetaclass(BaseModelMetaclass, pydantic.main.ModelMetaclass):
    @no_type_check
    def __new__(cls, name, bases, namespace, **kwargs):  # noqa C901
        BaseModelMetaclass.__new__(cls, name, bases, namespace, **kwargs)

        if (namespace.get("__module__"), namespace.get("__qualname__")) != (
            "odmantic.model",
            "Model",
        ):
            primary_field = None
            odm_fields: Dict[str, ODMBaseField] = namespace["__odm_fields__"]

            for field in odm_fields:
                if isinstance(field, ODMField) and field.primary_field:
                    # TODO handle inheritance with primary keys
                    if primary_field is not None:
                        raise TypeError(
                            f"cannot define multiple primary keys on model {name}"
                        )
                    primary_field = field.key_name

            if primary_field is None:
                primary_field = "id"
                odm_fields["id"] = ODMField(primary_field=True, key_name="_id")
                namespace["id"] = PDField(default_factory=_objectId)
                namespace["__annotations__"]["id"] = _objectId

            namespace["__primary_key__"] = primary_field

            if "__collection__" in namespace:
                collection_name = namespace["__collection__"]
                # https://docs.mongodb.com/manual/reference/limits/#Restriction-on-Collection-Names
                if "$" in collection_name:
                    raise TypeError(
                        f"Invalid collection name for {name}: cannot contain '$'"
                    )
                if collection_name == "":
                    raise TypeError(
                        f"Invalid collection name for {name}: cannot be empty"
                    )
                if collection_name.startswith("system."):
                    raise TypeError(
                        f"Invalid collection name for {name}:"
                        " cannot start with 'system.'"
                    )
            else:
                cls_name = name
                if cls_name.endswith("Model"):
                    # TODO document this
                    cls_name = cls_name[:-5]  # Strip Model in the class name
                namespace["__collection__"] = to_snake_case(cls_name)

        return pydantic.main.ModelMetaclass.__new__(
            cls, name, bases, namespace, **kwargs
        )


class EmbeddedModelMetaclass(BaseModelMetaclass, pydantic.main.ModelMetaclass):
    @no_type_check
    def __new__(cls, name, bases, namespace, **kwargs):  # noqa C901
        BaseModelMetaclass.__new__(cls, name, bases, namespace, **kwargs)

        if (namespace.get("__module__"), namespace.get("__qualname__")) != (
            "odmantic.model",
            "Model",
        ):
            odm_fields: Dict[str, ODMBaseField] = namespace["__odm_fields__"]

            for field in odm_fields:
                if isinstance(field, ODMField) and field.primary_field:
                    raise TypeError(
                        f"cannot define a primary field in {name} embedded document"
                    )

        return pydantic.main.ModelMetaclass.__new__(
            cls, name, bases, namespace, **kwargs
        )


TBase = TypeVar("TBase", bound="_BaseODMModel")


class _BaseODMModel(pydantic.BaseModel, metaclass=ABCMeta):
    if TYPE_CHECKING:
        __odm_fields__: ClassVar[Dict[str, ODMBaseField]] = {}
        __bson_serialized_fields__: ClassVar[FrozenSet[str]] = frozenset()
        __references__: ClassVar[Tuple[str, ...]] = ()

        __fields_modified__: Set[str] = set()

    __slots__ = ("__fields_modified__",)

    @classmethod
    def validate(cls: Type[TBase], value: Any) -> TBase:
        if isinstance(value, cls):
            # Do not copy the object as done in pydantic
            # This enable to keep the same python object
            return value
        return cast(TBase, super().validate(value))

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
        include: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        exclude: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        update: "DictStrAny" = None,
        deep: bool = False,
    ) -> TBase:
        # TODO implement
        raise NotImplementedError

    def __getstate__(self) -> Dict[Any, Any]:
        return {
            **super().__getstate__(),
            "__fields_modified__": self.__fields_modified__,
        }

    def __setstate__(self, state: Dict[Any, Any]) -> None:
        super().__setstate__(state)
        object.__setattr__(self, "__fields_modified__", state["__fields_modified__"])

    def doc(self, include: Optional["AbstractSetIntStr"] = None) -> Dict[str, Any]:
        """
        Generate a document representation of the instance (as a dictionary)
        """
        raw_doc = self.dict()
        doc: Dict[str, Any] = {}
        for field_name, field in self.__odm_fields__.items():
            if include is not None and field_name not in include:
                continue
            if isinstance(field, ODMReference):
                doc[field.key_name] = raw_doc[field_name]["id"]
            else:
                print(self.__bson_serialized_fields__)
                if field_name in self.__bson_serialized_fields__:
                    doc[field.key_name] = self.__fields__[field_name].type_.to_bson(
                        raw_doc[field_name]
                    )
                else:
                    doc[field.key_name] = raw_doc[field_name]
        return doc

    @classmethod
    def parse_doc(cls: Type[TBase], raw_doc: Dict) -> TBase:
        doc: Dict[str, Any] = {}
        for field_name, field in cls.__odm_fields__.items():
            if isinstance(field, ODMReference):
                doc[field_name] = field.model.parse_doc(raw_doc[field.key_name])
            else:
                doc[field_name] = raw_doc[field.key_name]
        instance = cls.parse_obj(doc)
        return cast(TBase, instance)


T = TypeVar("T", bound="Model")


class Model(_BaseODMModel, metaclass=ModelMetaclass):
    if TYPE_CHECKING:
        __collection__: ClassVar[str] = ""
        __primary_key__: ClassVar[str] = ""

        id: Union[_objectId, Any]  # TODO fix basic id field typing

    def __init__(__odmantic_self__, **data):
        super().__init__(**data)
        # Uses something other than `self` the first arg to allow "self" as a settable
        # attribute
        object.__setattr__(
            __odmantic_self__,
            "__fields_modified__",
            set(__odmantic_self__.__odm_fields__.keys()),
        )

    def __setattr__(self, name, value):
        if name == self.__primary_key__:
            # TODO implement
            raise NotImplementedError(
                "Reassigning a new primary key is not supported yet"
            )
        super().__setattr__(name, value)
        self.__fields_modified__.add(name)

    def __init_subclass__(cls):
        for name, field in cls.__odm_fields__.items():
            setattr(cls, name, field)


class EmbeddedModel(_BaseODMModel, metaclass=EmbeddedModelMetaclass):
    ...
