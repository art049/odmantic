import re
from abc import ABCMeta
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
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
)

import pydantic
from pydantic.error_wrappers import ValidationError
from pydantic.fields import Field as PDField
from pydantic.fields import FieldInfo as PDFieldInfo
from pydantic.fields import Undefined
from pydantic.tools import parse_obj_as
from pydantic.typing import resolve_annotations
from pydantic.utils import lenient_issubclass

from odmantic.bson_fields import _SUBSTITUTION_TYPES, BSONSerializedField, _objectId
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


def find_duplicate_key(fields: Iterable[ODMBaseField]) -> Optional[str]:
    seen: Set[str] = set()
    for f in fields:
        if f.key_name in seen:
            return f.key_name
        seen.add(f.key_name)
    return None


class BaseModelMetaclass(ABCMeta):
    def __new__(  # noqa C901
        cls,
        name: str,
        bases: Tuple[type, ...],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ) -> "BaseModelMetaclass":
        if namespace.get("__module__") != "odmantic.model" and namespace.get(
            "__qualname__"
        ) not in ("Model", "EmbeddedModel"):
            annotations = resolve_annotations(
                namespace.get("__annotations__", {}), namespace.get("__module__")
            )
            odm_fields: Dict[str, ODMBaseField] = {}
            references: List[str] = []
            bson_serialized_fields: Set[str] = set()

            # Make sure all fields are defined with type annotation
            for field_name, value in namespace.items():
                if (
                    not isinstance(value, UNTOUCHED_TYPES)
                    and is_valid_odm_field(field_name)
                    and field_name not in annotations
                ):
                    raise TypeError(
                        f"field {field_name} is defined without type annotation"
                    )

            # TODO handle class vars
            # Substitute bson types
            for k, v in annotations.items():
                subst_type = _SUBSTITUTION_TYPES.get(v)
                if subst_type is not None:
                    annotations[k] = subst_type

            # Handle special BSON serialized types
            for (field_name, field_type) in annotations.items():
                if (
                    is_valid_odm_field(field_name)
                    and not lenient_issubclass(field_type, UNTOUCHED_TYPES)
                    and lenient_issubclass(field_type, BSONSerializedField)
                ):
                    bson_serialized_fields.add(field_name)

            # Validate fields
            for (field_name, field_type) in annotations.items():
                value = namespace.get(field_name, Undefined)

                if (
                    not is_valid_odm_field(field_name)
                    or lenient_issubclass(field_type, UNTOUCHED_TYPES)
                    or isinstance(value, UNTOUCHED_TYPES)
                ):
                    continue

                if isinstance(value, PDFieldInfo):
                    raise TypeError(
                        "please use odmantic.Field instead of pydantic.Field"
                    )

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
                    key_name = (
                        value.key_name if value.key_name is not None else field_name
                    )
                    raise_on_invalid_key_name(key_name)
                    odm_fields[field_name] = ODMReference(
                        model=field_type, key_name=key_name
                    )
                    references.append(field_name)
                else:
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

        return cast("BaseModelMetaclass", super().__new__(cls, name, bases, namespace))


class ModelMetaclass(BaseModelMetaclass, pydantic.main.ModelMetaclass):
    def __new__(  # noqa C901
        cls,
        name: str,
        bases: Tuple[type, ...],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ) -> "ModelMetaclass":
        super().__new__(cls, name, bases, namespace, **kwargs)

        if (namespace.get("__module__"), namespace.get("__qualname__")) != (
            "odmantic.model",
            "Model",
        ):
            primary_field: Optional[str] = None
            odm_fields: Dict[str, ODMBaseField] = namespace["__odm_fields__"]

            for field in odm_fields.values():
                if isinstance(field, ODMField) and field.primary_field:
                    primary_field = field.key_name
                    break

            if primary_field is None:
                if "id" in odm_fields:
                    raise TypeError(
                        "can't automatically generate a primary field since an 'id' "
                        "field already exists"
                    )
                primary_field = "id"
                odm_fields["id"] = ODMField(primary_field=True, key_name="_id")
                namespace["id"] = PDField(default_factory=_objectId)
                namespace["__annotations__"]["id"] = _objectId

            namespace["__primary_key__"] = primary_field

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

        return cast(
            "ModelMetaclass",
            pydantic.main.ModelMetaclass.__new__(cls, name, bases, namespace, **kwargs),
        )


class EmbeddedModelMetaclass(BaseModelMetaclass, pydantic.main.ModelMetaclass):
    def __new__(  # noqa C901
        cls,
        name: str,
        bases: Tuple[type, ...],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ) -> "EmbeddedModelMetaclass":
        super().__new__(cls, name, bases, namespace, **kwargs)

        if (namespace.get("__module__"), namespace.get("__qualname__")) != (
            "odmantic.model",
            "EmbeddedModel",
        ):
            odm_fields: Dict[str, ODMBaseField] = namespace["__odm_fields__"]

            for field in odm_fields.values():
                if isinstance(field, ODMField) and field.primary_field:
                    raise TypeError(
                        f"cannot define a primary field in {name} embedded document"
                    )

        return cast(
            "EmbeddedModelMetaclass",
            pydantic.main.ModelMetaclass.__new__(cls, name, bases, namespace, **kwargs),
        )


TBase = TypeVar("TBase", bound="_BaseODMModel")


class _BaseODMModel(pydantic.BaseModel, metaclass=ABCMeta):
    if TYPE_CHECKING:
        __odm_fields__: ClassVar[Dict[str, ODMBaseField]] = {}
        __bson_serialized_fields__: ClassVar[FrozenSet[str]] = frozenset()
        __references__: ClassVar[Tuple[str, ...]] = ()

        __fields_modified__: Set[str] = set()

    __slots__ = ("__fields_modified__",)

    class Config:
        validate_all = True
        validate_assignment = True

    def __init_subclass__(cls) -> None:
        # FIXME move this into the metaclass ?
        if cls.__name__ not in ("Model", "EmbeddedModel"):
            for name, field in cls.__odm_fields__.items():
                setattr(cls, name, FieldProxy(parent=None, field=field))

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
                if field_name in self.__bson_serialized_fields__:
                    doc[field.key_name] = self.__fields__[field_name].type_.to_bson(
                        raw_doc[field_name]
                    )
                else:
                    doc[field.key_name] = raw_doc[field_name]
        return doc

    @classmethod
    def parse_doc(cls: Type[TBase], raw_doc: Dict) -> TBase:
        """Parse a BSON document into an instance of the Model

        Args:
            cls (Type[TBase]): [description]
            raw_doc (Dict): [description]

        Returns:
            TBase: [description]
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
    if TYPE_CHECKING:
        __collection__: ClassVar[str] = ""
        __primary_key__: ClassVar[str] = ""

        id: Union[_objectId, Any]  # TODO fix basic id field typing

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
        if name == self.__primary_key__:
            # TODO implement
            raise NotImplementedError(
                "Reassigning a new primary key is not supported yet"
            )
        super().__setattr__(name, value)


class EmbeddedModel(_BaseODMModel, metaclass=EmbeddedModelMetaclass):
    ...
