from __future__ import annotations

import datetime
import decimal
import enum
import pathlib
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
import pymongo
from pydantic import TypeAdapter, ValidationError
from pydantic._internal._decorators import PydanticDescriptorProxy
from pydantic.fields import Field as PDField
from pydantic.fields import FieldInfo as PDFieldInfo
from pydantic.main import BaseModel
from pydantic_core import InitErrorDetails
from typing_extensions import Literal, deprecated

from odmantic.bson import (
    _BSON_SUBSTITUTED_FIELDS,
    BaseBSONModel,
    ObjectId,
    _get_bson_serializer,
)
from odmantic.config import ODMConfigDict, validate_config
from odmantic.exceptions import (
    DocumentParsingError,
    IncorrectGenericEmbeddedModelValue,
    KeyNotFoundInDocumentError,
    ReferencedDocumentNotFoundError,
)
from odmantic.field import (
    Field,
    FieldProxy,
    ODMBaseField,
    ODMBaseIndexableField,
    ODMEmbedded,
    ODMEmbeddedGeneric,
    ODMField,
    ODMFieldInfo,
    ODMReference,
)
from odmantic.index import Index, ODMBaseIndex, ODMSingleFieldIndex
from odmantic.reference import ODMReferenceInfo
from odmantic.typing import (
    GenericAlias,
    dataclass_transform,
    get_args,
    get_first_type_argument_subclassing,
    get_origin,
    is_classvar,
    is_type_argument_subclass,
    lenient_issubclass,
    resolve_annotations,
)
from odmantic.utils import (
    Undefined,
    is_dunder,
    raise_on_invalid_collection_name,
    raise_on_invalid_key_name,
    to_snake_case,
)

if TYPE_CHECKING:
    from odmantic.typing import (
        AbstractSetIntStr,
        DictStrAny,
        IncEx,
        MappingIntStrAny,
        ReprArgs,
    )


UNTOUCHED_TYPES = (
    FunctionType,
    property,
    classmethod,
    staticmethod,
    PydanticDescriptorProxy,
)


def should_touch_field(value: Any = None, type_: Optional[Type] = None) -> bool:
    return not (
        lenient_issubclass(type_, UNTOUCHED_TYPES)
        or isinstance(value, UNTOUCHED_TYPES)
        or (type_ is not None and is_classvar(type_))
    )


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
    decimal.Decimal,
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
        is_immutable = type_ is None or (
            lenient_issubclass(type_, _IMMUTABLE_TYPES)
            and not lenient_issubclass(type_, EmbeddedModel)
        )
        return not is_immutable


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

    type_origin: Optional[Type] = get_origin(type_)
    if type_origin is not None and type_origin is not Literal:
        type_args: Tuple[Type, ...] = get_args(type_)
        new_arg_types = tuple(validate_type(subtype) for subtype in type_args)
        # FIXME: remove this hack when a better solution to handle dynamic
        # generics is found
        # https://github.com/pydantic/pydantic/issues/8354
        if type_origin is Union:
            new_root = Union[
                int, str
            ]  # We don't care about int,str since they will be replaced
            setattr(new_root, "__args__", new_arg_types)
            type_ = new_root  # type: ignore
        else:
            type_ = GenericAlias(type_origin, new_arg_types)  # type: ignore
    return type_


class BaseModelMetaclass(pydantic._internal._model_construction.ModelMetaclass):
    @staticmethod
    def __validate_cls_namespace__(  # noqa C901
        name: str, namespace: Dict[str, Any]
    ) -> None:
        """Validate the class name space in place"""
        annotations = resolve_annotations(
            namespace.get("__annotations__", {}), namespace.get("__module__")
        )
        config = validate_config(namespace.get("model_config", ODMConfigDict()), name)
        odm_fields: Dict[str, ODMBaseField] = {}
        references: List[str] = []
        bson_serializers: Dict[str, Callable[[Any], Any]] = {}
        mutable_fields: Set[str] = set()

        # Make sure all fields are defined with type annotation
        for field_name, value in namespace.items():
            if (
                should_touch_field(value=value)
                and not is_dunder(field_name)
                and field_name not in annotations
                and not field_name.startswith("model_")
            ):
                raise TypeError(
                    f"field {field_name} is defined without type annotation"
                )

        # Validate fields types and substitute bson fields
        for field_name, field_type in annotations.items():
            if not is_dunder(field_name) and should_touch_field(type_=field_type):
                substituted_type = validate_type(field_type)
                annotations[field_name] = substituted_type
                # Handle BSON serialized fields after substitution to allow some
                # builtin substitutions
                bson_serializer = _get_bson_serializer(substituted_type)
                if bson_serializer is not None:
                    bson_serializers[field_name] = bson_serializer

        # Validate fields
        for field_name, field_type in annotations.items():
            value = namespace.get(field_name, Undefined)

            if is_dunder(field_name) or not should_touch_field(value, field_type):
                continue  # pragma: no cover
                # https://github.com/nedbat/coveragepy/issues/198

            if isinstance(value, PDFieldInfo):
                raise TypeError("please use odmantic.Field instead of pydantic.Field")

            if is_type_mutable(field_type):
                mutable_fields.add(field_name)

            if lenient_issubclass(field_type, EmbeddedModel):
                if isinstance(value, ODMFieldInfo):
                    namespace[field_name] = value.pydantic_field_info
                    key_name = (
                        value.key_name if value.key_name is not None else field_name
                    )
                    primary_field = value.primary_field
                    index = value.index
                    unique = value.unique
                else:
                    key_name = field_name
                    primary_field = False
                    index = False
                    unique = False

                odm_fields[field_name] = ODMEmbedded(
                    primary_field=primary_field,
                    model=field_type,
                    key_name=key_name,
                    model_config=config,
                    index=index,
                    unique=unique,
                )

            elif is_type_argument_subclass(field_type, EmbeddedModel):
                if isinstance(value, ODMFieldInfo):
                    if value.primary_field:
                        raise TypeError(
                            "Declaring a generic type of embedded models as a primary "
                            f"field is not allowed: {field_name} in {name}"
                        )
                    namespace[field_name] = value.pydantic_field_info
                    key_name = (
                        value.key_name if value.key_name is not None else field_name
                    )
                    index = value.index
                    unique = value.unique
                else:
                    key_name = field_name
                    index = False
                    unique = False
                model = get_first_type_argument_subclassing(field_type, EmbeddedModel)
                assert model is not None
                if len(model.__references__) > 0:
                    raise TypeError(
                        "Declaring a generic type of embedded models containing "
                        f"references is not allowed: {field_name} in {name}"
                    )
                generic_origin = get_origin(field_type)
                assert generic_origin is not None
                odm_fields[field_name] = ODMEmbeddedGeneric(
                    model=model,
                    generic_origin=generic_origin,
                    key_name=key_name,
                    model_config=config,
                    index=index,
                    unique=unique,
                )

            elif lenient_issubclass(field_type, Model):
                if not isinstance(value, ODMReferenceInfo):
                    raise TypeError(
                        f"cannot define a reference {field_name} (in {name}) without"
                        " a Reference assigned to it"
                    )
                key_name = value.key_name if value.key_name is not None else field_name
                raise_on_invalid_key_name(key_name)
                odm_fields[field_name] = ODMReference(
                    model=field_type, key_name=key_name, model_config=config
                )
                references.append(field_name)
                del namespace[field_name]  # Remove default ODMReferenceInfo value
            else:
                if isinstance(value, ODMFieldInfo):
                    key_name = (
                        value.key_name if value.key_name is not None else field_name
                    )
                    raise_on_invalid_key_name(key_name)
                    odm_fields[field_name] = ODMField(
                        primary_field=value.primary_field,
                        key_name=key_name,
                        model_config=config,
                        index=value.index,
                        unique=value.unique,
                    )
                    namespace[field_name] = value.pydantic_field_info

                elif value is Undefined:
                    odm_fields[field_name] = ODMField(
                        primary_field=False, key_name=field_name, model_config=config
                    )

                else:
                    try:
                        TypeAdapter(field_type).validate_python(value)
                    except ValidationError:
                        raise TypeError(
                            f"Unhandled field definition {name}: {repr(field_type)}"
                            f" = {repr(value)}"
                        )
                    odm_fields[field_name] = ODMField(
                        primary_field=False, key_name=field_name, model_config=config
                    )

        # NOTE: Duplicate key detection make sur that at most one primary key is
        # defined
        duplicate_key = find_duplicate_key(odm_fields.values())
        if duplicate_key is not None:
            raise TypeError(f"Duplicated key_name: {duplicate_key} in {name}")

        namespace["__annotations__"] = annotations
        namespace["__odm_fields__"] = odm_fields
        namespace["__references__"] = tuple(references)
        namespace["__bson_serializers__"] = bson_serializers
        namespace["__mutable_fields__"] = frozenset(mutable_fields)
        namespace["model_config"] = config

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
            config: ODMConfigDict = namespace["model_config"]
            # Patch Model related fields to build a "pure" pydantic model
            odm_fields: Dict[str, ODMBaseField] = namespace["__odm_fields__"]
            for field_name, field in odm_fields.items():
                if isinstance(field, (ODMReference, ODMEmbedded)):
                    namespace["__annotations__"][
                        field_name
                    ] = field.model.__pydantic_model__
            # Build the pydantic model
            pydantic_cls = (
                pydantic._internal._model_construction.ModelMetaclass.__new__(
                    mcs,
                    f"{name}.__pydantic_model__",
                    (BaseBSONModel,),
                    namespace,
                    **kwargs,
                )
            )
            # Change the title to generate clean JSON schemas from this "pure" model
            if config["title"] is None:
                pydantic_cls.model_config["title"] = name
            cls.__pydantic_model__ = pydantic_cls

            for name, field in cls.__odm_fields__.items():
                field.bind_pydantic_field(cls.model_fields[name])
                setattr(cls, name, FieldProxy(parent=None, field=field))

        return cls


@dataclass_transform(kw_only_default=True, field_specifiers=(Field, ODMFieldInfo))
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
            config: ODMConfigDict = namespace["model_config"]
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
                odm_fields["id"] = ODMField(
                    primary_field=True, key_name="_id", model_config=config
                )
                namespace["id"] = PDField(default_factory=ObjectId)
                namespace["__annotations__"]["id"] = ObjectId

            namespace["__primary_field__"] = primary_field

            if config["collection"] is not None:
                collection_name = config["collection"]
            else:
                cls_name = name
                if cls_name.endswith("Model"):
                    # TODO document this
                    cls_name = cls_name[:-5]  # Strip Model in the class name
                collection_name = to_snake_case(cls_name)
            raise_on_invalid_collection_name(collection_name, cls_name=name)
            namespace["__collection__"] = collection_name

        return super().__new__(mcs, name, bases, namespace, **kwargs)

    def __pos__(cls) -> str:
        return cast(str, getattr(cls, "__collection__"))


@dataclass_transform(kw_only_default=True, field_specifiers=(Field, ODMFieldInfo))
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


BaseT = TypeVar("BaseT", bound="_BaseODMModel")


class _BaseODMModel(pydantic.BaseModel, metaclass=ABCMeta):
    """Base class for [Model][odmantic.model.Model] and
    [EmbeddedModel][odmantic.model.EmbeddedModel].

    !!! warning
        This internal class should never be instanciated directly.
    """

    if TYPE_CHECKING:
        __odm_fields__: ClassVar[Dict[str, ODMBaseField]] = {}
        __bson_serializers__: ClassVar[Dict[str, Callable[[Any], Any]]] = {}
        __mutable_fields__: ClassVar[FrozenSet[str]] = frozenset()
        __references__: ClassVar[Tuple[str, ...]] = ()
        __pydantic_model__: ClassVar[Type[BaseBSONModel]]
        # __fields_modified__ is not a ClassVar but this allows to hide this field from
        # the dataclass transform generated constructor
        __fields_modified__: ClassVar[Set[str]] = set()

    model_config: ClassVar[ODMConfigDict]

    __slots__ = ("__fields_modified__",)

    def __init__(self, **data: Any):
        super().__init__(**data)
        object.__setattr__(self, "__fields_modified__", set(self.__odm_fields__.keys()))

    @classmethod
    # TODO: rename to model_validate
    def validate(cls: Type[BaseT], value: Any) -> BaseT:
        if isinstance(value, cls):
            # Do not copy the object as done in pydantic
            # This enable to keep the same python object
            return value
        return super().model_validate(value)

    def __repr_args__(self) -> "ReprArgs":
        # Place the id field first in the repr string
        args = list(super().__repr_args__())
        id_arg = next((arg for arg in args if arg[0] == "id"), None)
        if id_arg is None:
            return args
        args.remove(id_arg)
        args = [id_arg] + args
        return args

    @deprecated(
        "copy is deprecated, please use model_copy instead",
    )
    def copy(
        self: BaseT,
        *,
        include: Union["AbstractSetIntStr", "MappingIntStrAny", None] = None,
        exclude: Union["AbstractSetIntStr", "MappingIntStrAny", None] = None,
        update: Dict[str, Any] | None = None,
        deep: bool = False,
    ) -> BaseT:
        if include is not None or exclude is not None:
            raise NotImplementedError(
                "copy with include or exclude is not supported anymore, "
                "please use `model_copy` instead"
            )
        return self.model_copy(update=update, deep=deep)

    def model_copy(
        self: BaseT,
        *,
        update: Optional["DictStrAny"] = None,
        deep: bool = False,
    ) -> BaseT:
        """Duplicate a model, optionally choose which fields to change.

        Danger:
            The data is not validated before creating the new model: **you should trust
            this data**.

        Arguments:
            update: values to change/add in the new model.
            deep: set to `True` to make a deep copy of the model

        Returns:
            new model instance

        """
        copied = super().model_copy(update=update, deep=deep)
        copied._post_copy_update()
        return copied

    def _post_copy_update(self: BaseT) -> None:
        """Recursively update internal fields of the copied model after it has been
        copied.

        Set them as if they were modified to make sure they are saved in the database.
        """
        object.__setattr__(self, "__fields_modified__", set(self.model_fields))
        for field_name, field in self.__odm_fields__.items():
            if isinstance(field, ODMEmbedded):
                value = getattr(self, field_name)
                value._post_copy_update()

    @deprecated(
        "update is deprecated, please use model_update instead",
    )
    def update(
        self,
        patch_object: Union[BaseModel, Dict[str, Any]],
        *,
        include: "IncEx" = None,
        exclude: "IncEx" = None,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> None:
        self.model_update(
            patch_object,
            include=include,
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    def model_update(
        self,
        patch_object: Union[BaseModel, Dict[str, Any]],
        *,
        include: "IncEx" = None,
        exclude: "IncEx" = None,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> None:
        """Update instance fields from a Pydantic model or a dictionary.

        If a pydantic model is provided, only the **fields set** will be
        applied by default.

        Args:
            patch_object: object containing the values to update
            include: fields to include from the `patch_object` (include all fields if
                `None`)
            exclude: fields to exclude from the `patch_object`, this takes
                precedence over include
            exclude_unset: only update fields explicitly set in the patch object (only
                applies to Pydantic models)
            exclude_defaults: only update fields that are different from their default
                value in the patch object (only applies to Pydantic models)
            exclude_none: only update fields different from None in the patch object
                (only applies to Pydantic models)

        Raises:
            ValidationError: the modifications would make the instance invalid

        <!--
        #noqa: DAR402 ValidationError
        -->
        """
        if isinstance(patch_object, BaseModel):
            patch_dict = patch_object.model_dump(
                include=include,
                exclude=exclude,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        else:
            odm_fields = set(self.__odm_fields__.keys())
            patch_dict = {}
            for k, v in patch_object.items():
                if include is not None and k not in include:
                    continue
                if exclude is not None and k in exclude:
                    continue
                if k not in odm_fields:
                    continue
                patch_dict[k] = v
        patched_instance_dict = {**self.model_dump(), **patch_dict}
        # FIXME: improve performance by only running updated field validators and then
        # model validators
        patched_instance = self.validate(patched_instance_dict)
        for name, new_value in patched_instance.__dict__.items():
            if self.__dict__[name] != new_value:
                # Manually change the field to avoid running the validators again
                self.__dict__[name] = new_value
                self.model_fields_set.add(name)
                self.__fields_modified__.add(name)

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        self.__fields_modified__.add(name)

    @deprecated(
        "doc is deprecated, please use model_dump_doc instead",
    )
    def doc(self, include: Optional["AbstractSetIntStr"] = None) -> Dict[str, Any]:
        return self.model_dump_doc(include=include)

    def model_dump_doc(
        self, include: Optional["AbstractSetIntStr"] = None
    ) -> Dict[str, Any]:
        """Generate a document (BSON) representation of the instance (as a dictionary).

        Args:
            include: field that should be included; if None, every fields will be
                included

        Returns:
            the document associated to the instance
        """
        raw_doc = self.model_dump()
        doc = self.__doc(raw_doc, type(self), include)
        return doc

    def __doc(  # noqa C901 # TODO: refactor document generation
        self,
        raw_doc: Dict[str, Any],
        model: Type["_BaseODMModel"],
        include: Optional["AbstractSetIntStr"] = None,
    ) -> Dict[str, Any]:
        doc: Dict[str, Any] = {}
        for field_name, field in model.__odm_fields__.items():
            if include is not None and field_name not in include:
                continue
            if isinstance(field, ODMReference):
                doc[field.key_name] = raw_doc[field_name][field.model.__primary_field__]
            elif isinstance(field, ODMEmbedded):
                doc[field.key_name] = self.__doc(raw_doc[field_name], field.model, None)
            elif isinstance(field, ODMEmbeddedGeneric):
                if field.generic_origin is dict:
                    doc[field.key_name] = {
                        item_key: self.__doc(item_value, field.model)
                        for item_key, item_value in raw_doc[field_name].items()
                    }
                else:
                    doc[field.key_name] = [
                        self.__doc(item, field.model) for item in raw_doc[field_name]
                    ]
            elif field_name in model.__bson_serializers__:
                doc[field.key_name] = model.__bson_serializers__[field_name](
                    raw_doc[field_name]
                )
            else:
                doc[field.key_name] = raw_doc[field_name]

        if model.model_config["extra"] == "allow":
            # raw_doc is indexed by field name so we compare against odm field names
            extras = set(raw_doc.keys()) - set(self.__odm_fields__.keys())
            for extra in extras:
                value = raw_doc[extra]
                subst_type = validate_type(type(value))
                bson_serializer = _get_bson_serializer(subst_type)
                if bson_serializer is not None:
                    doc[extra] = bson_serializer(value)
                else:
                    doc[extra] = value
        return doc

    @classmethod
    @deprecated(
        "parse_doc is deprecated, please use model_validate_doc instead",
    )
    def parse_doc(cls: Type[BaseT], raw_doc: Dict) -> BaseT:
        return cls.model_validate_doc(raw_doc)

    @classmethod
    def model_validate_doc(cls: Type[BaseT], raw_doc: Dict) -> BaseT:
        """Parse a BSON document into an instance of the Model

        Args:
            raw_doc: document to parse (as Dict)

        Raises:
            DocumentParsingError: the specified document is invalid

        Returns:
            an instance of the Model class this method is called on.
        """
        errors, obj = cls._parse_doc_to_obj(raw_doc)
        if len(errors) > 0:
            raise DocumentParsingError(
                errors=errors,
                model=cls,
            )
        try:
            instance = cls.model_validate(obj)
        except ValidationError as e:
            raise DocumentParsingError(
                errors=e.errors(),  # type: ignore
                model=cls,
            )

        return instance

    @classmethod
    def _parse_doc_to_obj(  # noqa C901 # TODO: refactor document parsing
        cls: Type[BaseT], raw_doc: Dict, base_loc: Tuple[str, ...] = ()
    ) -> Tuple[List[InitErrorDetails], Dict[str, Any]]:
        errors: List[InitErrorDetails] = []
        obj: Dict[str, Any] = {}
        for field_name, field in cls.__odm_fields__.items():
            if isinstance(field, ODMReference):
                sub_doc = raw_doc.get(field.key_name)
                if sub_doc is None:
                    errors.append(
                        InitErrorDetails(
                            type=ReferencedDocumentNotFoundError(field.key_name),
                            loc=base_loc + (field_name,),
                            input=raw_doc,
                        )
                    )

                else:
                    sub_errors, sub_obj = field.model._parse_doc_to_obj(
                        sub_doc, base_loc=base_loc + (field_name,)
                    )
                    errors.extend(sub_errors)
                    obj[field_name] = sub_obj
            elif isinstance(field, ODMEmbedded):
                value = raw_doc.get(field.key_name, Undefined)
                if value is not Undefined:
                    sub_errors, value = field.model._parse_doc_to_obj(
                        value, base_loc=base_loc + (field_name,)
                    )
                    errors.extend(sub_errors)
                else:
                    if not field.is_required_in_doc():
                        value = field.get_default_importing_value()
                    if value is Undefined:
                        errors.append(
                            InitErrorDetails(
                                type=KeyNotFoundInDocumentError(field.key_name),
                                loc=base_loc + (field_name,),
                                input=raw_doc,
                            )
                        )

                obj[field_name] = value
            elif isinstance(field, ODMEmbeddedGeneric):
                value = Undefined
                raw_value = raw_doc.get(field.key_name, Undefined)
                if raw_value is not Undefined:
                    if isinstance(raw_value, list) and (
                        field.generic_origin is list
                        or field.generic_origin is tuple
                        or field.generic_origin is set
                    ):
                        value = []
                        for i, item in enumerate(raw_value):
                            sub_errors, item = field.model._parse_doc_to_obj(
                                item, base_loc=base_loc + (field_name, f"[{i}]")
                            )
                            if len(sub_errors) > 0:
                                errors.extend(sub_errors)
                            else:
                                value.append(item)
                        obj[field_name] = value
                    elif isinstance(raw_value, dict) and field.generic_origin is dict:
                        value = {}
                        for item_key, item_value in raw_value.items():
                            sub_errors, item_value = field.model._parse_doc_to_obj(
                                item_value,
                                base_loc=base_loc + (field_name, f'["{item_key}"]'),
                            )
                            if len(sub_errors) > 0:
                                errors.extend(sub_errors)
                            else:
                                value[item_key] = item_value
                        obj[field_name] = value
                    else:
                        errors.append(
                            InitErrorDetails(
                                type=IncorrectGenericEmbeddedModelValue(raw_value),
                                loc=base_loc + (field_name,),
                                input=raw_doc,
                            )
                        )

                else:
                    if not field.is_required_in_doc():
                        value = field.get_default_importing_value()
                    if value is Undefined:
                        errors.append(
                            InitErrorDetails(
                                type=KeyNotFoundInDocumentError(field.key_name),
                                loc=base_loc + (field_name,),
                                input=raw_doc,
                            )
                        )
                    else:
                        obj[field_name] = value
            else:
                field = cast(ODMField, field)
                value = raw_doc.get(field.key_name, Undefined)
                if value is Undefined and not field.is_required_in_doc():
                    value = field.get_default_importing_value()

                if value is Undefined:
                    errors.append(
                        InitErrorDetails(
                            type=KeyNotFoundInDocumentError(field.key_name),
                            loc=base_loc + (field_name,),
                            input=raw_doc,
                        )
                    )
                else:
                    obj[field_name] = value

        if cls.model_config["extra"] == "allow":
            extras = set(raw_doc.keys()) - set(obj.keys())
            for extra in extras:
                obj[extra] = raw_doc[extra]

        return errors, obj


class Model(_BaseODMModel, metaclass=ModelMetaclass):
    """Class that can be extended to create an ODMantic Model.

    Each model will be bound to a MongoDB collection. You can customize the collection
    name by setting the `__collection__` class variable in the model classes.
    """

    if TYPE_CHECKING:
        __collection__: ClassVar[str] = ""
        __primary_field__: ClassVar[str] = ""

        id: Union[ObjectId, Any] = Field()  # TODO fix basic id field typing

    def __setattr__(self, name: str, value: Any) -> None:
        if name == self.__primary_field__:
            # TODO implement
            raise NotImplementedError(
                "Reassigning a new primary key is not supported yet"
            )
        super().__setattr__(name, value)

    @classmethod
    def __indexes__(cls) -> Tuple[Union[ODMBaseIndex, pymongo.IndexModel], ...]:
        indexes: List[Union[ODMBaseIndex, pymongo.IndexModel]] = []
        for field in cls.__odm_fields__.values():
            if isinstance(field, ODMBaseIndexableField) and (
                field.index or field.unique
            ):
                indexes.append(
                    ODMSingleFieldIndex(
                        key_name=field.key_name,
                        unique=field.unique,
                    )
                )
        get_indexes_from_config = cls.model_config["indexes"]
        if get_indexes_from_config is not None:
            for index in get_indexes_from_config():
                indexes.append(
                    index.to_odm_index() if isinstance(index, Index) else index
                )
        return tuple(indexes)

    @deprecated(
        "update is deprecated, please use model_update instead",
    )
    def update(
        self,
        patch_object: Union[BaseModel, Dict[str, Any]],
        *,
        include: "IncEx" = None,
        exclude: "IncEx" = None,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> None:
        return self.model_update(
            patch_object,
            include=include,
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    def model_update(
        self,
        patch_object: Union[BaseModel, Dict[str, Any]],
        *,
        include: "IncEx" = None,
        exclude: "IncEx" = None,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> None:
        is_primary_field_in_patch = (
            isinstance(patch_object, BaseModel)
            and self.__primary_field__ in patch_object.model_fields
        ) or (isinstance(patch_object, dict) and self.__primary_field__ in patch_object)
        if is_primary_field_in_patch:
            if (
                include is None
                and (exclude is None or self.__primary_field__ not in exclude)
            ) or (
                include is not None
                and self.__primary_field__ in include
                and (exclude is None or self.__primary_field__ not in exclude)
            ):
                raise ValueError(
                    "Updating the primary key is not supported. "
                    "See the copy method if you want to modify the primary field."
                )
        return super().model_update(
            patch_object,
            include=include,
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )


class EmbeddedModel(_BaseODMModel, metaclass=EmbeddedModelMetaclass):
    """Class that can be extended to create an ODMantic Embedded Model.

    An embedded document cannot be persisted directly to the database but should be
    integrated in a regular ODMantic Model.
    """
