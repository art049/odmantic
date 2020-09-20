import re
from typing import TYPE_CHECKING, Any, Dict, Pattern, Sequence, Union

if TYPE_CHECKING:
    from odmantic.fields import FieldProxy


class QueryExpression(Dict[str, Any]):
    # def __repr__(self):
    #     parent_repr = super().__repr__()
    #     if parent_repr == "{}":
    #         parent_repr = ""
    #     return f"QueryExpression({parent_repr})"

    def __or__(self, other: "QueryExpression") -> "QueryExpression":
        return or_(self, other)

    def __and__(self, other: "QueryExpression") -> "QueryExpression":
        return and_(self, other)

    def __invert__(self) -> "QueryExpression":
        return not_(self)


def and_(*elements: Union[QueryExpression, bool]) -> QueryExpression:
    return QueryExpression({"$and": elements})


def or_(*elements: Union[QueryExpression, bool]) -> QueryExpression:
    return QueryExpression({"$or": elements})


def nor_(*elements: Union[QueryExpression, bool]) -> QueryExpression:
    return QueryExpression({"$nor": elements})


def not_(element: Union[QueryExpression, bool]) -> QueryExpression:
    # TODO clarify usage and test
    return QueryExpression({"$not": element})


def _cmp_expression(f: "FieldProxy", op: str, cmp_value: Any) -> QueryExpression:

    # FIXME 🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮
    from odmantic.model import EmbeddedModel

    if isinstance(cmp_value, EmbeddedModel):
        value = cmp_value.doc()
    else:
        value = cmp_value
    return QueryExpression({+f: {op: value}})


FieldProxyAny = Union["FieldProxy", Any]


def eq(field: FieldProxyAny, value: Any) -> QueryExpression:
    return _cmp_expression(field, "$eq", value)


def ne(field: FieldProxyAny, value: Any) -> QueryExpression:
    return _cmp_expression(field, "$ne", value)


def gt(field: FieldProxyAny, value: Any) -> QueryExpression:
    return _cmp_expression(field, "$gt", value)


def gte(field: FieldProxyAny, value: Any) -> QueryExpression:
    return _cmp_expression(field, "$gte", value)


def lt(field: FieldProxyAny, value: Any) -> QueryExpression:
    return _cmp_expression(field, "$lt", value)


def lte(field: FieldProxyAny, value: Any) -> QueryExpression:
    return _cmp_expression(field, "$lte", value)


def in_(field: FieldProxyAny, value: Sequence) -> QueryExpression:
    return _cmp_expression(field, "$in", value)


def not_in(field: FieldProxyAny, value: Sequence) -> QueryExpression:
    return _cmp_expression(field, "$nin", value)


def exists(field: FieldProxyAny) -> QueryExpression:
    return _cmp_expression(field, "$exists", True)


def not_exists(field: FieldProxyAny) -> QueryExpression:
    return _cmp_expression(field, "$exists", False)


def match(field: FieldProxyAny, pattern: Union[Pattern, str]) -> QueryExpression:
    # FIXME might create incompatibilities
    # https://docs.mongodb.com/manual/reference/operator/query/regex/#regex-and-not
    if isinstance(pattern, str):
        r = re.compile(pattern)
    else:
        r = pattern
    return QueryExpression({+field: r})
