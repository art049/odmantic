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
        """Search for Model instances matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            sort: sort expression
            skip: number of document to skip
            limit: maximum number of instance fetched

        Returns:
            [odmantic.engine.AIOCursor][] of the query

        """
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
        """Search for a Model instance matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            sort: sort expression

        Raises:
            DocumentParsingError: unable to parse the resulting document

        Returns:
            the fetched instance if found otherwise None

        <!---
        #noqa: DAR402 DocumentParsingError
        -->
        """
        return await self.engine.find_one(
            model, *queries, sort=sort, session=self.engine._get_session(self)
        )

    async def count(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[QueryExpression, Dict, bool],
    ) -> int:
        """Get the count of documents matching a query

        Args:
            model: model to perform the operation on
            *queries: query filters to apply

        Returns:
            number of document matching the query
        """
        return await self.engine.count(
            model, *queries, session=self.engine._get_session(self)
        )

    async def save(
        self,
        instance: ODMEngine.ModelType,
    ) -> ODMEngine.ModelType:
        """Persist an instance to the database

        This method behaves as an 'upsert' operation. If a document already exists
        with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be saved as well.

        Args:
            instance: instance to persist

        Returns:
            the saved instance

        NOTE:
            The save operation actually modify the instance argument in place. However,
            the instance is still returned for convenience.
        """
        return await self.engine.save(instance, session=self.engine._get_session(self))

    async def save_all(
        self,
        instances: Sequence[ODMEngine.ModelType],
    ) -> List[ODMEngine.ModelType]:
        """Persist instances to the database

        This method behaves as multiple 'upsert' operations. If one of the document
        already exists with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be recursively saved as
        well.

        Args:
            instances: instances to persist

        Returns:
            the saved instances

        NOTE:
            The save_all operation actually modify the arguments in place. However, the
            instances are still returned for convenience.
        """
        return await self.engine.save_all(
            instances, session=self.engine._get_session(self)
        )

    async def delete(
        self,
        instance: ODMEngine.ModelType,
    ) -> None:
        """Delete an instance from the database

        Args:
            instance: the instance to delete

        Raises:
            DocumentNotFoundError: the instance has not been persisted to the database

        <!---
        #noqa: DAR402 DocumentNotFoundError
        #noqa: DAR201
        -->
        """
        return await self.engine.delete(
            instance, session=self.engine._get_session(self)
        )

    async def remove(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[QueryExpression, Dict, bool],
        just_one: bool = False,
    ) -> int:
        """Delete Model instances matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            just_one: limit the deletion to just one document

        Returns:
            the number of instances deleted from the database.
        """
        return await self.engine.remove(
            model, *queries, just_one=just_one, session=self.engine._get_session(self)
        )


class AIOSession(AIOSessionBase, AsyncContextManager):
    """An AsyncIO session object for ordering sequential operations.


    Sessions can be created from the engine directly by using the
    [AIOEngine.session][odmantic.engine.AIOEngine.session] method.

    Example usage as a context manager:
    ```python
    engine = AIOEngine(...)
    async with engine.session() as session:
        john = await session.find(User, User.name == "John")
        john.name = "Doe"
        await session.save(john)
    ```

    Example raw usage:
    ```python
    engine = AIOEngine(...)
    session = engine.session()
    await session.start()
    john = await session.find(User, User.name == "John")
    john.name = "Doe"
    await session.save(john)
    await session.end()
    ```
    """

    def __init__(self, engine: ODMEngine.AIOEngine):
        self.engine = engine
        self.session: Optional[AsyncIOMotorClientSession] = None

    @property
    def is_started(self) -> bool:
        return self.session is not None

    def get_driver_session(self) -> AsyncIOMotorClientSession:
        """Return the underlying Motor Session"""
        if self.session is None:
            raise RuntimeError("session not started")
        return self.session

    async def start(self) -> None:
        """Start the logical Mongo session."""
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
        """Create a transaction in the existing session"""
        return AIOTransaction(self)


class AIOTransaction(AIOSessionBase, AsyncContextManager):
    """A transaction object to aggregate sequential operations.

    Transactions can be created from the engine using the
    [AIOEngine.transaction][odmantic.engine.AIOEngine.transaction]
    method or they can be created during an existing session by using
    [AIOSession.transaction][odmantic.session.AIOSession.transaction].

    Example usage as a context manager:
    ```python
    engine = AIOEngine(...)
    async with engine.transaction() as transaction:
        john = await transaction.find(User, User.name == "John")
        john.name = "Doe"
        await transaction.save(john)
        await transaction.commit()
    ```

    Example raw usage:
    ```python
    engine = AIOEngine(...)
    transaction = engine.transaction()
    await transaction.start()
    john = await transaction.find(User, User.name == "John")
    john.name = "Doe"
    await transaction.save(john)
    await transaction.commit()
    ```

    Warning:
        MongoDB transaction are only supported on replicated clusters: either directly a
        replicaSet or a sharded cluster with replication enabled.
    """

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
        """Return the underlying Motor Session"""
        if not self._transaction_started:
            raise RuntimeError("transaction not started")
        return self.session.get_driver_session()

    async def start(self) -> None:
        """Initiate the transaction."""
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
        """Commit the changes and close the transaction."""
        if not self._transaction_started:
            raise RuntimeError("Transaction not started")
        assert self.session.session is not None
        await self.session.session.commit_transaction()
        self._transaction_started = False
        if not self._session_provided:
            await self.session.end()

    async def abort(self) -> None:
        """Discard the changes and drop the transaction"""
        if not self._transaction_started:
            raise RuntimeError("Transaction not started")
        assert self.session.session is not None
        await self.session.session.abort_transaction()
        self._transaction_started = False
        if not self._session_provided:
            await self.session.end()

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
        """Search for Model instances matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            sort: sort expression
            skip: number of document to skip
            limit: maximum number of instance fetched

        Returns:
            [odmantic.engine.SyncCursor][] of the query

        """
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
        """Search for a Model instance matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            sort: sort expression

        Raises:
            DocumentParsingError: unable to parse the resulting document

        Returns:
            the fetched instance if found otherwise None

        <!---
        #noqa: DAR402 DocumentParsingError
        -->
        """
        return self.engine.find_one(
            model, *queries, sort=sort, session=self.engine._get_session(self)
        )

    def count(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[QueryExpression, Dict, bool],
    ) -> int:
        """Get the count of documents matching a query

        Args:
            model: model to perform the operation on
            *queries: query filters to apply

        Returns:
            number of document matching the query
        """
        return self.engine.count(
            model, *queries, session=self.engine._get_session(self)
        )

    def save(
        self,
        instance: ODMEngine.ModelType,
    ) -> ODMEngine.ModelType:
        """Persist an instance to the database

        This method behaves as an 'upsert' operation. If a document already exists
        with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be saved as well.

        Args:
            instance: instance to persist

        Returns:
            the saved instance

        NOTE:
            The save operation actually modify the instance argument in place. However,
            the instance is still returned for convenience.
        """
        return self.engine.save(instance, session=self.engine._get_session(self))

    def save_all(
        self,
        instances: Sequence[ODMEngine.ModelType],
    ) -> List[ODMEngine.ModelType]:
        """Persist instances to the database

        This method behaves as multiple 'upsert' operations. If one of the document
        already exists with the same primary key, it will be overwritten.

        All the other models referenced by this instance will be recursively saved as
        well.

        Args:
            instances: instances to persist

        Returns:
            the saved instances

        NOTE:
            The save_all operation actually modify the arguments in place. However, the
            instances are still returned for convenience.
        """
        return self.engine.save_all(instances, session=self.engine._get_session(self))

    def delete(
        self,
        instance: ODMEngine.ModelType,
    ) -> None:
        """Delete an instance from the database

        Args:
            instance: the instance to delete

        Raises:
            DocumentNotFoundError: the instance has not been persisted to the database

        <!---
        #noqa: DAR402 DocumentNotFoundError
        #noqa: DAR201
        -->
        """
        return self.engine.delete(instance, session=self.engine._get_session(self))

    def remove(
        self,
        model: Type[ODMEngine.ModelType],
        *queries: Union[QueryExpression, Dict, bool],
        just_one: bool = False,
    ) -> int:
        """Delete Model instances matching the query filter provided

        Args:
            model: model to perform the operation on
            *queries: query filter to apply
            just_one: limit the deletion to just one document

        Returns:
            the number of instances deleted from the database.

        """
        return self.engine.remove(
            model, *queries, just_one=just_one, session=self.engine._get_session(self)
        )


class SyncSession(SyncSessionBase, ContextManager):
    """A session object for ordering sequential operations.

    Sessions can be created from the engine directly by using the
    [SyncEngine.session][odmantic.engine.SyncEngine.session] method.

    Example usage as a context manager:
    ```python
    engine = SyncEngine(...)
    with engine.session() as session:
        john = session.find(User, User.name == "John")
        john.name = "Doe"
        session.save(john)
    ```

    Example raw usage:
    ```python
    engine = SyncEngine(...)
    session = engine.session()
    session.start()
    john = session.find(User, User.name == "John")
    john.name = "Doe"
    session.save(john)
    session.end()
    ```
    """

    def __init__(self, engine: ODMEngine.SyncEngine):
        self.engine = engine
        self.session: Optional[ClientSession] = None

    @property
    def is_started(self) -> bool:
        return self.session is not None

    def get_driver_session(self) -> ClientSession:
        """Return the underlying PyMongo Session"""
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
        """Create a transaction in the existing session"""
        return SyncTransaction(self)


class SyncTransaction(SyncSessionBase, ContextManager):
    """A transaction object to aggregate sequential operations.

    Transactions can be created from the engine using the
    [SyncEngine.transaction][odmantic.engine.SyncEngine.transaction]
    method or they can be created during an existing session by using
    [SyncSession.transaction][odmantic.session.SyncSession.transaction].

    Example usage as a context manager:
    ```python
    engine = SyncEngine(...)
    with engine.transaction() as transaction:
        john = transaction.find(User, User.name == "John")
        john.name = "Doe"
        transaction.save(john)
        transaction.commit()
    ```

    Example raw usage:
    ```python
    engine = SyncEngine(...)
    transaction = engine.transaction()
    transaction.start()
    john = transaction.find(User, User.name == "John")
    john.name = "Doe"
    transaction.save(john)
    transaction.commit()
    ```

    Warning:
        MongoDB transaction are only supported on replicated clusters: either directly a
        replicaSet or a sharded cluster with replication enabled.
    """

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
        """Return the underlying PyMongo Session"""
        if not self._transaction_started:
            raise RuntimeError("transaction not started")
        return self.session.get_driver_session()

    def start(self) -> None:
        """Initiate the transaction."""
        if self._transaction_started:
            raise RuntimeError("Transaction already started")
        if not self._session_provided:
            self.session.start()
        assert self.session.session is not None
        self._transaction_context = self.session.session.start_transaction().__enter__()
        self._transaction_started = True

    def commit(self) -> None:
        """Commit the changes and close the transaction."""
        if not self._transaction_started:
            raise RuntimeError("Transaction not started")
        assert self.session.session is not None
        self.session.session.commit_transaction()
        self._transaction_started = False
        if not self._session_provided:
            self.session.end()

    def abort(self) -> None:
        """Discard the changes and drop the transaction."""
        if not self._transaction_started:
            raise RuntimeError("Transaction not started")
        assert self.session.session is not None
        self.session.session.abort_transaction()
        self._transaction_started = False
        if not self._session_provided:
            self.session.end()

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
