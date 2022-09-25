import abc
from copy import deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    Optional,
    Pattern,
    Set,
    Type,
    Union,
    cast,
)

from pydantic.fields import Field as PDField
from pydantic.fields import FieldInfo, ModelField, Undefined

from odmantic.config import BaseODMConfig
from odmantic.query import (
    QueryExpression,
    SortExpression,
    asc,
    desc,
    eq,
    gt,
    gte,
    in_,
    lt,
    lte,
    match,
    ne,
    not_in,
)

from .typing import NoArgAnyCallable

if TYPE_CHECKING:
    from odmantic.model import EmbeddedModel, Model  # noqa: F401


def Field(
    default: Any = Undefined,
    *,
    key_name: Optional[str] = None,
    primary_field: bool = False,
    index: bool = False,
    unique: bool = False,
    default_factory: Optional[NoArgAnyCallable] = None,
    # alias: str = None, # FIXME not supported yet
    title: Optional[str] = None,
    description: Optional[str] = None,
    const: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    regex: Optional[str] = None,
    **extra: Any,
) -> Any:
    """Used to provide extra information about a field, either for the model schema or
    complex validation. Some arguments apply only to number fields (``int``, ``float``,
     ``Decimal``) and some apply only to ``str``.

    Tip:
        The main additions of ODMantic to the regular pydantic `Field` are the
        `key_name`, `index`, `unique` and the `primary_field` options.

    Warning:
        If both `default` and `default_factory` are set, an error is raised.

    Warning:
        `primary_field` can't be used along with `key_name` since the key_name will be
        set to `_id`.


    Args:
        default: since this is replacing the field’s default, its first argument is
            used to set the default, use ellipsis (``...``) to indicate the field has no
            default value
        key_name: the name to use in the the mongo document structure
        primary_field: this field should be considered as a primary key.
        index: this field should be considered as an index
        unique: this field should be considered as a unique index
        default_factory: callable that will be called when a default value is needed
            for this field.
        title: can be any string, used in the schema
        description: can be any string, used in the schema
        const: this field is required and *must* take it's default value
        gt: only applies to numbers, requires the field to be "greater than". The
            schema will have an ``exclusiveMinimum`` validation keyword
        ge: only applies to numbers, requires the field to be "greater than or equal
            to". The schema will have a ``minimum`` validation keyword
        lt: only applies to numbers, requires the field to be "less than". The schema
            will have an ``exclusiveMaximum`` validation keyword
        le: only applies to numbers, requires the field to be "less than or equal to"
            . The schema will have a ``maximum`` validation keyword
        multiple_of: only applies to numbers, requires the field to be "a multiple of
            ". The schema will have a ``multipleOf`` validation keyword
        min_items: only applies to sequences, requires the field to have a minimum
            item count.
        max_items: only applies to sequences, requires the field to have a maximum
            item count.
        min_length: only applies to strings, requires the field to have a minimum
            length. The schema will have a ``maximum`` validation keyword
        max_length: only applies to strings, requires the field to have a maximum
            length. The schema will have a ``maxLength`` validation keyword
        regex: only applies to strings, requires the field match agains a regular
            expression pattern string. The schema will have a ``pattern`` validation
            keyword
        **extra: any additional keyword arguments will be added as is to the schema

    <!---
    # noqa: DAR201
    # noqa: DAR003
    # noqa: DAR401
    # noqa: DAR101
    -->
    """
    # Perform casts on optional fields to avoid incompatibility due to the strict
    # optional mypy setting
    pydantic_field = PDField(
        default,
        default_factory=default_factory,
        # alias=alias,  # FIXME check aliases compatibility
        title=cast(str, title),
        description=cast(str, description),
        const=cast(bool, const),
        gt=cast(float, gt),
        ge=cast(float, ge),
        lt=cast(float, lt),
        le=cast(float, le),
        multiple_of=cast(float, multiple_of),
        min_items=cast(int, min_items),
        max_items=cast(int, max_items),
        min_length=cast(int, min_length),
        max_length=cast(int, max_length),
        regex=cast(str, regex),
        **extra,
    )
    if primary_field:
        if key_name is not None and key_name != "_id":
            raise ValueError(
                "cannot specify a primary field with a custom key_name,"
                "key_name='_id' enforced"
            )
        else:
            key_name = "_id"
    elif key_name == "_id":
        raise ValueError(
            "cannot specify key_name='_id' without defining the field as primary"
        )

    return ODMFieldInfo(
        pydantic_field_info=pydantic_field,
        primary_field=primary_field,
        key_name=key_name,
        index=index,
        unique=unique,
    )


class ODMFieldInfo:
    """Extra data for an ODM field."""

    __slots__ = ("pydantic_field_info", "primary_field", "key_name", "index", "unique")

    def __init__(
        self,
        *,
        pydantic_field_info: FieldInfo,
        primary_field: bool,
        key_name: Optional[str],
        index: bool,
        unique: bool,
    ):
        self.pydantic_field_info = pydantic_field_info
        self.primary_field = primary_field
        self.key_name = key_name
        self.index = index
        self.unique = unique


class ODMBaseField(metaclass=abc.ABCMeta):

    __slots__ = ("key_name", "model_config", "pydantic_field")
    __allowed_operators__: Set[str]

    def __init__(self, key_name: str, model_config: Type[BaseODMConfig]):
        self.key_name = key_name
        self.model_config = model_config

    def bind_pydantic_field(self, field: ModelField) -> None:
        self.pydantic_field = field

    def is_required_in_doc(self) -> bool:
        if self.model_config.parse_doc_with_default_factories:
            return self.pydantic_field.required  # type: ignore
        else:
            return (
                self.pydantic_field.default_factory is not None
                or self.pydantic_field.required  # type: ignore
            )


class ODMBaseIndexableField(ODMBaseField, metaclass=abc.ABCMeta):

    __slots__ = ("index", "unique")

    def __init__(
        self,
        key_name: str,
        model_config: Type[BaseODMConfig],
        index: bool,
        unique: bool,
    ):
        super().__init__(key_name, model_config)
        self.index = index
        self.unique = unique


class ODMField(ODMBaseIndexableField):
    """Used to interact with the ODM model class."""

    __slots__ = ("primary_field",)
    __allowed_operators__ = set(
        ("eq", "ne", "in_", "not_in", "lt", "lte", "gt", "gte", "match", "asc", "desc")
    )

    def __init__(
        self,
        *,
        key_name: str,
        model_config: Type["BaseODMConfig"],
        primary_field: bool,
        index: bool = False,
        unique: bool = False,
    ):
        super().__init__(key_name, model_config, index, unique)
        self.primary_field = primary_field

    def get_default_importing_value(self) -> Any:
        # The default importing value doesn't consider the default_factory setting by
        # default as it could result in inconsistent behaviors for datetime.now
        # factories for example
        if self.model_config.parse_doc_with_default_factories:
            return self.pydantic_field.get_default()

        if self.pydantic_field.default is None:
            # deepcopy is quite slow on None
            value = None
        else:
            value = deepcopy(self.pydantic_field.default)
        return value


class ODMReference(ODMBaseField):
    """Field pointing on a referenced model."""

    __slots__ = ("model",)
    __allowed_operators__ = set(("eq", "ne", "in_", "not_in"))

    def __init__(
        self, key_name: str, model_config: Type[BaseODMConfig], model: Type["Model"]
    ):
        super().__init__(key_name, model_config)
        self.model = model


class ODMEmbedded(ODMField):

    __slots__ = "model"
    __allowed_operators__ = set(("eq", "ne", "in_", "not_in"))

    def __init__(
        self,
        primary_field: bool,
        key_name: str,
        model_config: Type[BaseODMConfig],
        model: Type["EmbeddedModel"],
        index: bool = False,
        unique: bool = False,
    ):
        super().__init__(
            primary_field=primary_field,
            key_name=key_name,
            model_config=model_config,
            index=index,
            unique=unique,
        )
        self.model = model


class ODMEmbeddedGeneric(ODMField):
    # Only dict,set and list are "officially" supported for now
    __slots__ = ("model", "generic_origin")
    __allowed_operators__ = set(("eq", "ne"))

    def __init__(
        self,
        key_name: str,
        model_config: Type[BaseODMConfig],
        model: Type["EmbeddedModel"],
        generic_origin: Any,
        index: bool = False,
        unique: bool = False,
    ):
        super().__init__(
            primary_field=False,
            key_name=key_name,
            model_config=model_config,
            index=index,
            unique=unique,
        )
        self.model = model
        self.generic_origin = generic_origin


class KeyNameProxy(str):
    """Used to provide the `++` operator enabling reference key name creation"""

    def __pos__(self) -> str:
        return f"${self}"


class FieldProxy:
    __slots__ = ("parent", "field")

    def __init__(self, parent: Optional["FieldProxy"], field: ODMBaseField) -> None:
        self.parent = parent
        self.field = field

    def _get_key_name(self) -> str:
        parent: Optional[FieldProxy] = object.__getattribute__(self, "parent")
        field: ODMBaseField = object.__getattribute__(self, "field")

        if parent is None:
            return field.key_name

        parent_name: str = object.__getattribute__(parent, "_get_key_name")()
        return f"{parent_name}.{field.key_name}"

    def __getattribute__(self, name: str) -> Any:
        if name == "__class__":  # support `isinstance` for python < 3.7
            return super().__getattribute__(name)

        field: ODMBaseField = object.__getattribute__(self, "field")
        if isinstance(field, ODMReference):
            if name in field.model.__odm_fields__:
                raise NotImplementedError(
                    "filtering across references is not supported"
                )
        elif isinstance(field, ODMEmbedded):
            child_field = field.model.__odm_fields__.get(name)
            if child_field is None:
                try:
                    return super().__getattribute__(name)
                except AttributeError:
                    raise AttributeError(
                        f"attribute {name} not found in {field.model.__name__}"
                    )
            return FieldProxy(parent=self, field=child_field)

        if name not in field.__allowed_operators__:
            raise AttributeError(
                f"operator {name} not allowed for {type(field).__name__} fields"
            )
        return super().__getattribute__(name)

    def __pos__(self) -> KeyNameProxy:
        return KeyNameProxy(object.__getattribute__(self, "_get_key_name")())

    def __gt__(self, value: Any) -> QueryExpression:
        return self.gt(value)

    def gt(self, value: Any) -> QueryExpression:
        return gt(self, value)

    def gte(self, value: Any) -> QueryExpression:
        return gte(self, value)

    def __ge__(self, value: Any) -> QueryExpression:
        return self.gte(value)

    def lt(self, value: Any) -> QueryExpression:
        return lt(self, value)

    def __lt__(self, value: Any) -> QueryExpression:
        return self.lt(value)

    def lte(self, value: Any) -> QueryExpression:
        return lte(self, value)

    def __le__(self, value: Any) -> QueryExpression:
        return self.lte(value)

    def eq(self, value: Any) -> QueryExpression:
        return eq(self, value)

    def __eq__(self, value: Any) -> QueryExpression:  # type: ignore
        return self.eq(value)

    def ne(self, value: Any) -> QueryExpression:
        return ne(self, value)

    def __ne__(self, value: Any) -> QueryExpression:  # type: ignore
        return self.ne(value)

    def in_(self, value: Iterable) -> QueryExpression:
        return in_(self, value)

    def not_in(self, value: Iterable) -> QueryExpression:
        return not_in(self, value)

    def match(self, pattern: Union[Pattern, str]) -> QueryExpression:
        return match(self, pattern)

    def asc(self) -> SortExpression:
        return asc(self)

    def desc(self) -> SortExpression:
        return desc(self)
