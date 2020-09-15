from typing import TYPE_CHECKING, Any, Dict, Sequence, cast

if TYPE_CHECKING:
    from odmantic.fields import FieldProxy


class QueryExpression(Dict[str, Any]):
    def __repr__(self):
        parent_repr = super().__repr__()
        if parent_repr == "{}":
            parent_repr = ""
        return f"QueryExpression({parent_repr})"

    def __or__(self, other: "QueryExpression"):
        return or_(self, other)

    def __and__(self, other: "QueryExpression"):
        return and_(self, other)

    def __invert__(self):
        return not_(self)


def not_(element: QueryExpression) -> QueryExpression:
    return QueryExpression({"$not": element})


def and_(*elements: QueryExpression) -> QueryExpression:
    return QueryExpression({"$and": elements})


def or_(*elements: QueryExpression) -> QueryExpression:
    return QueryExpression({"$or": elements})


def nor_(*elements: QueryExpression) -> QueryExpression:
    return QueryExpression({"$nor": elements})


def _cmp_expression(f: "FieldProxy", op: str, value: Any) -> QueryExpression:

    # FIXME 🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮🤮
    from odmantic.model import EmbeddedModel

    if isinstance(value, EmbeddedModel):
        cast_value = cast(EmbeddedModel, value)
        value = cast_value.doc()

    return QueryExpression({+f: {op: value}})


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
