from typing import Any, Optional, Sequence


class _MISSING_TYPE:
    pass


MISSING_DEFAULT = _MISSING_TYPE()


def field(**kwargs) -> Any:
    return Field(**kwargs)


class Field:
    """Class providing mongodb field customization
    """

    def __init__(
        self,
        *,
        primary_key: bool = False,
        mongo_name: Optional[str] = None,
        default=MISSING_DEFAULT
    ):
        assert primary_key and (
            mongo_name != "_id" or mongo_name is None
        ), "Setting primary_key enforce the mongo_name to _id"
        self.primary_key = primary_key
        self.mongo_name = mongo_name  # actual field name in mongo
        self.default = default

    def __pos__(self):
        return self.mongo_name

    def __cmp_expression__(self, op: str, value: Any):
        return {self.mongo_name: {op: value}}

    def __eq__(self, value):
        return self.__cmp_expression__("$eq", value)

    def eq(self, value):
        return self.__eq__(value)

    def __ne__(self, value):
        return self.__cmp_expression__("$ne", value)

    def ne(self, value):
        return self.__ne__(value)

    def __gt__(self, value):
        return self.__cmp_expression__("$gt", value)

    def gt(self, value):
        return self.__gt__(value)

    def __ge__(self, value):
        return self.__cmp_expression__("$gte", value)

    def gte(self, value):
        return self.__ge__(value)

    def __le__(self, value):
        return self.__cmp_expression__("$le", value)

    def le(self, value):
        return self.__le__(value)

    def __lt__(self, value):
        return self.__cmp_expression__("$lte", value)

    def lte(self, value):
        return self.__lt__(value)

    def in_(self, value: Sequence):
        return self.__cmp_expression__("$in", value)

    def not_in(self, value: Sequence):
        return self.__cmp_expression__("$nin", value)

    def exists(self):
        return self.__cmp_expression__("$exists", True)

    def not_exists(self):
        return self.__cmp_expression__("$exists", False)
