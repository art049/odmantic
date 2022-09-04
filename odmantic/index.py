from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Optional, Sequence, Tuple, Union, cast

import pymongo

from odmantic.field import FieldProxy
from odmantic.query import FieldProxyAny, SortExpression, asc


class ODMBaseIndex(metaclass=ABCMeta):
    def __init__(self, unique: bool, index_name: Optional[str]) -> None:
        self.unique = unique
        self.index_name = index_name

    @abstractmethod
    def get_index_specifier(self) -> Sequence[Tuple[str, int]]:
        ...

    def get_pymongo_index(self) -> pymongo.IndexModel:
        kwargs: Dict[str, Any] = {"keys": self.get_index_specifier()}
        if self.index_name is not None:
            kwargs["name"] = self.index_name
        if self.unique:
            kwargs["unique"] = True
        return pymongo.IndexModel(**kwargs)


class ODMSingleFieldIndex(ODMBaseIndex):
    def __init__(self, key_name: str, unique: bool, index_name: Optional[str] = None):
        super().__init__(unique, index_name)
        self.key_name = key_name

    def get_index_specifier(self) -> Sequence[Tuple[str, int]]:
        return [
            (self.key_name, pymongo.ASCENDING),
        ]


class ODMCompoundIndex(ODMBaseIndex):
    def __init__(
        self,
        fields: Tuple[SortExpression, ...],
        unique: bool,
        index_name: Optional[str],
    ):
        super().__init__(unique, index_name)
        self.fields = fields

    def get_index_specifier(self) -> Sequence[Tuple[str, int]]:
        return [
            (
                list(f.keys())[0],
                pymongo.ASCENDING if list(f.values())[0] == 1 else pymongo.DESCENDING,
            )
            for f in self.fields
        ]


class Index:
    def __init__(
        self,
        *fields: Union[FieldProxyAny, SortExpression],
        unique: bool = False,
        name: Optional[str] = None
    ) -> None:
        """Declare an ODM index in the Model.Config.indexes generator.

        Example usage:
        ```python
        from odmantic import Model, Index
        from odmantic.query import desc

        class Player(Model):
            name: str
            score: int

            class Config:
                @staticmethod
                def indexes():
                    yield Index(Player.name, desc(Player.score))
        ```

        Args:
            *fields (Any | SortExpression | str): fields to build the index with
            unique: build a unique index
            name: specify an optional custom index name
        """
        self.fields = cast(Tuple[Union[SortExpression, FieldProxy], ...], fields)
        self.unique = unique
        self.name = name

    def to_odm_index(self) -> "ODMBaseIndex":
        if len(self.fields) == 1:
            field = self.fields[0]
            if isinstance(field, SortExpression):
                key_name = list(field.keys())[0]
            else:
                key_name = object.__getattribute__(field, "_get_key_name")()
            return ODMSingleFieldIndex(
                key_name, unique=self.unique, index_name=self.name
            )
        else:
            fields = tuple(
                (f if isinstance(f, SortExpression) else asc(f) for f in self.fields)
            )
            return ODMCompoundIndex(fields, unique=self.unique, index_name=self.name)
