from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Optional, Pattern, Sequence, Set, Type

from pydantic.fields import Field as PDField
from pydantic.fields import FieldInfo, Undefined

from odmantic.query import (
    QueryExpression,
    eq,
    exists,
    gt,
    gte,
    in_,
    le,
    lte,
    ne,
    not_exists,
    not_in,
)

from .typing import NoArgAnyCallable

if TYPE_CHECKING:
    from odmantic.model import Model, EmbeddedModel  # noqa: F401


def Field(
    default: Any = Undefined,
    *,
    key_name: str = None,
    primary_field: bool = False,
    default_factory: Optional[NoArgAnyCallable] = None,
    # alias: str = None, not supported yet
    title: str = None,
    description: str = None,
    const: bool = None,
    gt: float = None,
    ge: float = None,
    lt: float = None,
    le: float = None,
    multiple_of: float = None,
    min_items: int = None,
    max_items: int = None,
    min_length: int = None,
    max_length: int = None,
    regex: str = None,
    **extra: Any,
) -> Any:
    """
    Used to provide extra information about a field, either for the model schema or
    complex validation. Some arguments apply only to number fields (``int``, ``float``,
     ``Decimal``) and some apply only to ``str``.

    :param default: since this is replacing the field’s default, its first argument is
      used to set the default, use ellipsis (``...``) to indicate the field is required
    :param key_name: the name to use in the the document structure
    :param primary_field: this field should be considered as a primary key.
      Can't be used along with `key_name` since the key_name will be set to `_id`
    :param default_factory: callable that will be called when a default value is needed
      for this field.
      If both `default` and `default_factory` are set, an error is raised.
    :param alias: Not supported by odmantic yet (the public name of the field)
    :param title: can be any string, used in the schema
    :param description: can be any string, used in the schema
    :param const: this field is required and *must* take it's default value
    :param gt: only applies to numbers, requires the field to be "greater than". The
      schema will have an ``exclusiveMinimum`` validation keyword
    :param ge: only applies to numbers, requires the field to be "greater than or equal
      to". The schema will have a ``minimum`` validation keyword
    :param lt: only applies to numbers, requires the field to be "less than". The schema
      will have an ``exclusiveMaximum`` validation keyword
    :param le: only applies to numbers, requires the field to be "less than or equal to"
      . The schema will have a ``maximum`` validation keyword
    :param multiple_of: only applies to numbers, requires the field to be "a multiple of
      ". The schema will have a ``multipleOf`` validation keyword
    :param min_length: only applies to strings, requires the field to have a minimum
      length. The schema will have a ``maximum`` validation keyword
    :param max_length: only applies to strings, requires the field to have a maximum
      length. The schema will have a ``maxLength`` validation keyword
    :param regex: only applies to strings, requires the field match agains a regular
      expression pattern string. The schema will have a ``pattern`` validation keyword
    :param **extra: any additional keyword arguments will be added as is to the schema
    """
    pydantic_field = PDField(
        default,
        default_factory=default_factory,
        # alias=alias,  # FIXME check aliases compatibility
        title=title,
        description=description,
        const=const,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        min_items=min_items,
        max_items=max_items,
        min_length=min_length,
        max_length=max_length,
        regex=regex,
        **extra,
    )
    if primary_field:
        if key_name != "_id":
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
    )


class ODMFieldInfo:
    """Extra data for an ODM field"""

    __slots__ = ("pydantic_field_info", "primary_field", "key_name")

    def __init__(
        self,
        *,
        pydantic_field_info: FieldInfo,
        primary_field: bool,
        key_name: Optional[str],
    ):
        self.pydantic_field_info = pydantic_field_info
        self.primary_field = primary_field
        self.key_name = key_name


class ODMBaseField(metaclass=abc.ABCMeta):

    __slots__ = ("key_name",)
    __allowed_operators__: Set[str]

    def __init__(self, key_name: str):
        self.key_name = key_name


class ODMField(ODMBaseField):
    """Used to interact with the ODM model class"""

    __slots__ = ("primary_field",)
    __allowed_operators__ = set(
        (
            "eq",
            "ne",
            "in_",
            "not_in",
            "exists",
            "not_exists",
            "le",
            "lte",
            "gt",
            "gte",
            "match",
        )
    )

    def __init__(self, *, primary_field: bool, key_name: str):
        super().__init__(key_name)
        self.primary_field = primary_field


class ODMReference(ODMBaseField):
    """Field pointing"""

    __slots__ = ("model",)
    __allowed_operators__ = set(("eq", "ne", "in_", "not_in", "exists", "not_exists"))

    def __init__(self, key_name: str, model: Type["Model"]):
        super().__init__(key_name)
        self.model = model


class ODMEmbedded(ODMBaseField):

    __slots__ = ("model",)
    __allowed_operators__ = set(("eq", "ne", "in_", "not_in", "exists", "not_exists"))

    def __init__(self, key_name: str, model: Type["EmbeddedModel"]):
        super().__init__(key_name)
        self.model = model


class FieldProxy:
    __slots__ = ("parent", "field")

    def __init__(self, parent: Optional[FieldProxy], field: ODMBaseField) -> None:
        self.parent = parent
        self.field = field

    def _get_key_name(self):
        parent: Optional[FieldProxy] = object.__getattribute__(self, "parent")
        field: ODMBaseField = object.__getattribute__(self, "field")

        if parent is None:
            return field.key_name

        parent_name: str = object.__getattribute__(parent, "_get_key_name")()
        return f"{parent_name}.{field.key_name}"

    def __getattribute__(self, name: str) -> Any:
        field: ODMBaseField = object.__getattribute__(self, "field")
        if isinstance(field, ODMReference):
            try:
                return super().__getattribute__(name)
            except AttributeError:
                if name in field.model.__odm_fields__:
                    raise NotImplementedError(
                        "filtering across references is not supported"
                    )
                raise
        elif isinstance(field, ODMEmbedded):
            embedded_field = field.model.__odm_fields__.get(name)
            if embedded_field is None:
                try:
                    return super().__getattribute__(name)
                except AttributeError:
                    raise AttributeError(
                        f"attribute {name} not found in {field.model.__name__}"
                    )
            return FieldProxy(parent=self, field=embedded_field)

        if name not in field.__allowed_operators__:
            raise AttributeError(
                f"operator {name} not allowed for {type(field).__name__}"
            )
        return super().__getattribute__(name)

    def __pos__(self):
        return object.__getattribute__(self, "_get_key_name")()

    def __gt__(self, value):
        return self.gt(value)

    def gt(self, value) -> QueryExpression:
        return gt(self, value)

    def gte(self, value) -> QueryExpression:
        return gte(self, value)

    def __ge__(self, value):
        return self.gte(value)

    def le(self, value) -> QueryExpression:
        return le(self, value)

    def __le__(self, value):
        return self.le(value)

    def lte(self, value) -> QueryExpression:
        return lte(self, value)

    def __lt__(self, value):
        return self.lte(value)

    def eq(self, value) -> QueryExpression:
        return eq(self, value)

    def __eq__(self, value):
        return self.eq(value)

    def ne(self, value) -> QueryExpression:
        return ne(self, value)

    def __ne__(self, value):
        return self.ne(value)

    def in_(self, value: Sequence) -> QueryExpression:
        return in_(self, value)

    def not_in(self, value: Sequence) -> QueryExpression:
        return not_in(self, value)

    def exists(self) -> QueryExpression:
        # TODO handle None/null ?
        return exists(self)

    def not_exists(self) -> QueryExpression:
        return not_exists(self)

    def match(self, pattern: Pattern):
        # FIXME might create incompatibilities
        # https://docs.mongodb.com/manual/reference/operator/query/regex/#regex-and-not
        return QueryExpression({self.key_name: pattern})
