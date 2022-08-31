from __future__ import annotations

from abc import ABCMeta
from datetime import datetime
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    ContextManager,
    Dict,
    Generic,
    Optional,
    Type,
    TypeVar,
)

from motor.motor_asyncio import AsyncIOMotorClientSession
from pymongo.client_session import ClientSession

import odmantic.engine as ODMEngine
from odmantic.model import Model
from odmantic.query import QueryExpression

T = TypeVar("T", bound=Model)


class BaseUpdater(Generic[T], metaclass=ABCMeta):
    model: Type[T]
    query: QueryExpression
    just_one: bool
    update_dict: Dict[str, Any]

    def __init__(
        self,
        model: Type[T],
        query: QueryExpression,
        just_one: bool = False,
    ) -> None:
        object.__setattr__(self, "model", model)
        object.__setattr__(self, "query", query)
        object.__setattr__(self, "just_one", just_one)
        object.__setattr__(self, "update_dict", {})

    def __setattr__(self, name: str, value: Any) -> None:
        update_dict = self.update_dict
        if "$set" not in update_dict:
            update_dict["$set"] = {}
        update_dict["$set"][name] = value


class AIOUpdater(BaseUpdater[T], AsyncContextManager[T]):
    engine: ODMEngine.AIOEngine
    session: Optional[AsyncIOMotorClientSession]

    def __init__(
        self,
        model: Type[T],
        engine: ODMEngine.AIOEngine,
        session: Optional[AsyncIOMotorClientSession],
        query: QueryExpression,
        just_one: bool = False,
    ) -> None:
        super().__init__(model, query, just_one=just_one)
        object.__setattr__(self, "engine", engine)
        object.__setattr__(self, "session", session)

    async def __aenter__(self) -> T:
        return await super().__aenter__()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if exc_type is not None:
            return

        collection = self.engine.get_collection(self.model)
        if self.just_one:
            await collection.update_one(
                self.query, self.update_dict, session=self.session
            )
        else:
            await collection.update_many(
                self.query, self.update_dict, session=self.session
            )


class SyncUpdater(BaseUpdater[T], ContextManager[T]):
    engine: ODMEngine.SyncEngine
    session: Optional[ClientSession]

    def __init__(
        self,
        model: Type[T],
        engine: ODMEngine.SyncEngine,
        session: Optional[ClientSession],
        query: QueryExpression,
        just_one: bool = False,
    ) -> None:
        super().__init__(model, query, just_one=just_one)
        object.__setattr__(self, "engine", engine)
        object.__setattr__(self, "session", session)

    def __enter__(self) -> T:
        return super().__enter__()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if exc_type is not None:
            return

        collection = self.engine.get_collection(self.model)
        if self.just_one:
            collection.update_one(self.query, self.update_dict, session=self.session)
        else:
            collection.update_many(self.query, self.update_dict, session=self.session)


def currentDate() -> datetime:
    ...
