from __future__ import annotations

from abc import ABCMeta
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    ContextManager,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
    Union,
)

from motor.motor_asyncio import AsyncIOMotorClientSession
from pymongo.client_session import ClientSession

import odmantic.engine as ODMEngine
from odmantic.query import QueryExpression


class AIOSessionBase(metaclass=ABCMeta):
    engine: ODMEngine.AIOEngine

    def find(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[
            QueryExpression, Dict, bool
        ],  # bool: allow using binary operators with mypy
        sort: Optional[Any] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> ODMEngine.AIOCursor[ODMEngine.ModelType]:
        return self.engine.find(
            model,
            *queries,
            sort=sort,
            skip=skip,
            limit=limit,
            session=self.engine._get_session(self),
        )

    async def find_one(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[
            QueryExpression, Dict, bool
        ],  # bool: allow using binary operators w/o plugin
        sort: Optional[Any] = None,
    ) -> Optional[ODMEngine.ModelType]:
        return await self.engine.find_one(
            model, *queries, sort=sort, session=self.engine._get_session(self)
        )

    async def count(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[QueryExpression, Dict, bool],
    ) -> int:
        return await self.engine.count(
            model, *queries, session=self.engine._get_session(self)
        )

    async def save(
        self,
        instance: ODMEngine.ModelType,
    ) -> ODMEngine.ModelType:
        return await self.engine.save(instance, session=self.engine._get_session(self))

    async def save_all(
        self,
        instances: Sequence[ODMEngine.ModelType],
    ) -> List[ODMEngine.ModelType]:
        return await self.engine.save_all(
            instances, session=self.engine._get_session(self)
        )

    async def delete(
        self,
        instance: ODMEngine.ModelType,
    ) -> None:
        return await self.engine.delete(
            instance, session=self.engine._get_session(self)
        )

    async def remove(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[QueryExpression, Dict, bool],
        just_one: bool = False,
    ) -> int:
        return await self.engine.remove(
            model, *queries, just_one=just_one, session=self.engine._get_session(self)
        )


class AIOSession(AIOSessionBase, AsyncContextManager):
    def __init__(self, engine: ODMEngine.AIOEngine):
        self.engine = engine
        self.session: Optional[AsyncIOMotorClientSession] = None

    @property
    def is_started(self) -> bool:
        return self.session is not None

    def get_driver_session(self) -> AsyncIOMotorClientSession:
        if self.session is None:
            raise RuntimeError("session not started")
        return self.session

    async def start(self) -> None:
        """Start the logical session."""
        if self.is_started:
            raise RuntimeError("Session is already started")
        self.session = await self.engine.client.start_session()

    async def end(self) -> None:
        """Finish the logical session."""
        if self.session is None:
            raise RuntimeError("Session is not started")
        await self.session.end_session()
        self.session = None

    async def __aenter__(self) -> "AIOSession":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.end()

    def transaction(self) -> AIOTransaction:
        return AIOTransaction(self)


class AIOTransaction(AIOSessionBase, AsyncContextManager):
    def __init__(self, context: Union[ODMEngine.AIOEngine, ODMEngine.AIOSession]):
        self._session_provided = isinstance(context, ODMEngine.AIOSession)
        if self._session_provided:
            assert isinstance(context, ODMEngine.AIOSession)
            if not context.is_started:
                raise RuntimeError("provided session is not started")
            self.session = context
            self.engine = context.engine
        else:
            assert isinstance(context, ODMEngine.AIOEngine)
            self.session = AIOSession(context)
            self.engine = context

        self._transaction_started = False
        self._transaction_context: Optional[AsyncContextManager] = None

    def get_driver_session(self) -> AsyncIOMotorClientSession:
        if not self._transaction_started:
            raise RuntimeError("transaction not started")
        return self.session.get_driver_session()

    async def start(self) -> None:
        if self._transaction_started:
            raise RuntimeError("Transaction already started")
        if not self._session_provided:
            await self.session.start()
        assert self.session.session is not None
        self._transaction_context = (
            await self.session.session.start_transaction().__aenter__()
        )
        self._transaction_started = True

    async def commit(self) -> None:
        if not self._transaction_started:
            raise RuntimeError("Transaction not started")
        assert self.session.session is not None
        await self.session.session.commit_transaction()
        self._transaction_started = False

    async def abort(self) -> None:
        if not self._transaction_started:
            raise RuntimeError("Transaction not started")
        assert self.session.session is not None
        await self.session.session.abort_transaction()
        self._transaction_started = False

    async def __aenter__(self) -> "AIOTransaction":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        assert self._transaction_context is not None
        await self._transaction_context.__aexit__(exc_type, exc, traceback)
        self._transaction_started = False
        if not self._session_provided:
            await self.session.end()


class SyncSessionBase(metaclass=ABCMeta):
    engine: ODMEngine.SyncEngine

    def find(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[
            QueryExpression, Dict, bool
        ],  # bool: allow using binary operators with mypy
        sort: Optional[Any] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> ODMEngine.SyncCursor[ODMEngine.ModelType]:
        return self.engine.find(
            model,
            *queries,
            sort=sort,
            skip=skip,
            limit=limit,
            session=self.engine._get_session(self),
        )

    def find_one(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[
            QueryExpression, Dict, bool
        ],  # bool: allow using binary operators w/o plugin
        sort: Optional[Any] = None,
    ) -> Optional[ODMEngine.ModelType]:
        return self.engine.find_one(
            model, *queries, sort=sort, session=self.engine._get_session(self)
        )

    def count(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[QueryExpression, Dict, bool],
    ) -> int:
        return self.engine.count(
            model, *queries, session=self.engine._get_session(self)
        )

    def save(
        self,
        instance: ODMEngine.ModelType,
    ) -> ODMEngine.ModelType:
        return self.engine.save(instance, session=self.engine._get_session(self))

    def save_all(
        self,
        instances: Sequence[ODMEngine.ModelType],
    ) -> List[ODMEngine.ModelType]:
        return self.engine.save_all(instances, session=self.engine._get_session(self))

    def delete(
        self,
        instance: ODMEngine.ModelType,
    ) -> None:
        return self.engine.delete(instance, session=self.engine._get_session(self))

    def remove(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[QueryExpression, Dict, bool],
        just_one: bool = False,
    ) -> int:
        return self.engine.remove(
            model, *queries, just_one=just_one, session=self.engine._get_session(self)
        )


class SyncSession(SyncSessionBase, ContextManager):
    def __init__(self, engine: ODMEngine.SyncEngine):
        self.engine = engine
        self.session: Optional[ClientSession] = None

    @property
    def is_started(self) -> bool:
        return self.session is not None

    def get_driver_session(self) -> ClientSession:
        if self.session is None:
            raise RuntimeError("session not started")
        return self.session

    def start(self) -> None:
        """Start the logical session."""
        if self.is_started:
            raise RuntimeError("Session is already started")
        self.session = self.engine.client.start_session()

    def end(self) -> None:
        """Finish the logical session."""
        if self.session is None:
            raise RuntimeError("Session is not started")
        self.session.end_session()
        self.session = None

    def __enter__(self) -> "SyncSession":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.end()

    def transaction(self) -> SyncTransaction:
        return SyncTransaction(self)


class SyncTransaction(SyncSessionBase, ContextManager):
    def __init__(self, context: Union[ODMEngine.SyncEngine, ODMEngine.SyncSession]):
        self._session_provided = isinstance(context, ODMEngine.SyncSession)
        if self._session_provided:
            assert isinstance(context, ODMEngine.SyncSession)
            if not context.is_started:
                raise RuntimeError("provided session is not started")
            self.session = context
            self.engine = context.engine
        else:
            assert isinstance(context, ODMEngine.SyncEngine)
            self.session = SyncSession(context)
            self.engine = context

        self._transaction_started = False
        self._transaction_context: Optional[ContextManager] = None

    def get_driver_session(self) -> ClientSession:
        if not self._transaction_started:
            raise RuntimeError("transaction not started")
        return self.session.get_driver_session()

    def start(self) -> None:
        if self._transaction_started:
            raise RuntimeError("Transaction already started")
        if not self._session_provided:
            self.session.start()
        assert self.session.session is not None
        self._transaction_context = self.session.session.start_transaction().__enter__()
        self._transaction_started = True

    def commit(self) -> None:
        if not self._transaction_started:
            raise RuntimeError("Transaction not started")
        assert self.session.session is not None
        self.session.session.commit_transaction()
        self._transaction_started = False

    def abort(self) -> None:
        if not self._transaction_started:
            raise RuntimeError("Transaction not started")
        assert self.session.session is not None
        self.session.session.abort_transaction()
        self._transaction_started = False

    def __enter__(self) -> "SyncTransaction":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        assert self._transaction_context is not None
        self._transaction_context.__exit__(exc_type, exc, traceback)
        self._transaction_started = False
        if not self._session_provided:
            self.session.end()
