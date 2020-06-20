from __future__ import annotations

from typing import Any, Dict, Optional, Pattern, Sequence


class _MISSING_TYPE:
    pass


MISSING_DEFAULT = _MISSING_TYPE()


def field(**kwargs) -> Any:
    return Field(**kwargs)


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


class Field:
    """Class providing mongodb field customization
    """

    def __init__(
        self,
        *,
        primary_key: bool = False,
        mongo_name: Optional[str] = None,  # TODO Should not be optional
        default: Any = MISSING_DEFAULT
    ):
        assert not primary_key or (
            mongo_name == "_id" or mongo_name is None
        ), "Setting primary_key enforce the mongo_name to _id"
        self.primary_key = primary_key
        self.mongo_name = mongo_name  # actual field name in mongo
        self.default = default

    def __pos__(self):
        return self.mongo_name

    def __cmp_expression__(self, op: str, value: Any) -> QueryExpression:
        return QueryExpression({self.mongo_name: {op: value}})

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
        return QueryExpression({self.mongo_name: pattern})


def Reference() -> Any:
    ...
