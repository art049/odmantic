from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Sequence

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


def _cmp_expression(f: ODMField, op: str, value: Any):
    return {f.key_name: {op: value}}


def eq(field, value):
    return _cmp_expression(field, "$eq", value)


def ne(field, value):
    return _cmp_expression(field, "$ne", value)


def gt(field, value):
    return _cmp_expression(field, "$gt", value)


def gte(field, value):
    return _cmp_expression(field, "$gte", value)


def le(field, value):
    return _cmp_expression(field, "$le", value)


def lte(field, value):
    return _cmp_expression(field, "$lte", value)


def in_(field, value: Sequence):
    return _cmp_expression(field, "$in", value)


def not_in(field, value: Sequence):
    return _cmp_expression(field, "$nin", value)


def exists(field):
    return _cmp_expression(field, "$exists", True)


def not_exists(field):
    return _cmp_expression(field, "$exists", False)
