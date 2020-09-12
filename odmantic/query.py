from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Sequence, cast

from pydantic.utils import lenient_issubclass

if TYPE_CHECKING:
    from .fields import ODMField


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


def not_(element):
    return {"$not": element}


def and_(*elements):
    return {"$and": elements}


def or_(*elements):
    return {"$or": elements}


def nor_(*elements):
    return {"$nor": elements}


def _cmp_expression(f: ODMField, op: str, value: Any) -> QueryExpression:
    # FIXME 🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮
    from odmantic.model import EmbeddedModel

    if lenient_issubclass(type(value), EmbeddedModel):
        cast_value = cast(EmbeddedModel, value)
        value = cast_value.doc()
    return QueryExpression({f.key_name: {op: value}})


def eq(field, value) -> QueryExpression:
    return _cmp_expression(field, "$eq", value)


def ne(field, value) -> QueryExpression:
    return _cmp_expression(field, "$ne", value)


def gt(field, value) -> QueryExpression:
    return _cmp_expression(field, "$gt", value)


def gte(field, value) -> QueryExpression:
    return _cmp_expression(field, "$gte", value)


def le(field, value) -> QueryExpression:
    return _cmp_expression(field, "$le", value)


def lte(field, value) -> QueryExpression:
    return _cmp_expression(field, "$lte", value)


def in_(field, value: Sequence) -> QueryExpression:
    return _cmp_expression(field, "$in", value)


def not_in(field, value: Sequence) -> QueryExpression:
    return _cmp_expression(field, "$nin", value)


def exists(field) -> QueryExpression:
    return _cmp_expression(field, "$exists", True)


def not_exists(field) -> QueryExpression:
    return _cmp_expression(field, "$exists", False)
