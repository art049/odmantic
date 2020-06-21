from __future__ import annotations

from typing import Any, Dict, Optional, Pattern, Sequence

from pydantic.fields import Field as PDField
from pydantic.fields import FieldInfo, Undefined

from .typing import NoArgAnyCallable


class QueryExpression(Dict[str, Any]):
    @staticmethod
    def or_(*expressions: QueryExpression):
        return QueryExpression({"$or": expressions})

    def __or__(self, other: QueryExpression):
        return QueryExpression.or_(self, other)

    @staticmethod
    def and_(*expressions: QueryExpression):
        return QueryExpression({"$and": expressions})

    def __and__(self, other: QueryExpression):
        return QueryExpression.and_(self, other)

    @staticmethod
    def not_(expression: QueryExpression):
        return QueryExpression({"$not": expression})

    def __invert__(self):
        return QueryExpression.not_(self)

    @staticmethod
    def nor_(*expressions: QueryExpression):
        return QueryExpression({"$nor": expressions})


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
    complex valiation. Some arguments apply only to number fields (``int``, ``float``,
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


class ODMField:
    """Used to interact with the ODM model class"""

    def __init__(self, *, primary_field: bool, key_name: str):
        self.primary_field = primary_field
        self.key_name = key_name  # actual field name in mongo

    def __pos__(self):
        return self.key_name

    def __cmp_expression__(self, op: str, value: Any) -> QueryExpression:
        return QueryExpression({self.key_name: {op: value}})

    def __eq__(self, value):
        return self.eq(value)

    def eq(self, value) -> QueryExpression:
        return self.__cmp_expression__("$eq", value)

    def __ne__(self, value):
        return self.ne(value)

    def ne(self, value) -> QueryExpression:
        return self.__cmp_expression__("$ne", value)

    def __gt__(self, value):
        return self.gt(value)

    def gt(self, value) -> QueryExpression:
        return self.__cmp_expression__("$gt", value)

    def __ge__(self, value):
        return self.gte(value)

    def gte(self, value) -> QueryExpression:
        return self.__cmp_expression__("$gte", value)

    def __le__(self, value):
        return self.le(value)

    def le(self, value) -> QueryExpression:
        return self.__cmp_expression__("$le", value)

    def __lt__(self, value):
        return self.lte(value)

    def lte(self, value) -> QueryExpression:
        return self.__cmp_expression__("$lte", value)

    def in_(self, value: Sequence) -> QueryExpression:
        return self.__cmp_expression__("$in", value)

    def not_in(self, value: Sequence) -> QueryExpression:
        return self.__cmp_expression__("$nin", value)

    def exists(self) -> QueryExpression:
        return self.__cmp_expression__("$exists", True)

    def not_exists(self) -> QueryExpression:
        return self.__cmp_expression__("$exists", False)

    def match(self, pattern: Pattern):
        # FIXME might create incompatibilities
        # https://docs.mongodb.com/manual/reference/operator/query/regex/#regex-and-not
        return QueryExpression({self.key_name: pattern})


def Reference() -> Any:
    ...
