import os
from typing import Any, Callable, Optional

from pymongo import AsyncMongoClient

from . import AsyncSingletonHubMeta
from .environment_hub import EnvironmentHubMeta


class AsyncMongoHubMeta(
    EnvironmentHubMeta[AsyncMongoClient],
    AsyncSingletonHubMeta[AsyncMongoClient],
):
    """Async counterpart of :class:`MongoHubMeta`.

    Builds pymongo's native ``AsyncMongoClient`` (pymongo 4.9+, no motor). The
    accessor is synchronous; only the operations are awaited. Because closing an
    async client is itself a coroutine, teardown is the async ``aclear`` /
    ``aclear_all`` (which close *and* clear the cache) — awaited inside the
    running event loop.
    """

    _formats = EnvironmentHubMeta._bake_basic_uri_formats(
        "MONGO",
        "MONGO_DB",
        "MONGODB",
    )
    _kwargs: dict = {}
    _logger: Optional[Callable[..., Any]] = print

    def _value_selector(cls, name: str):
        client = AsyncMongoClient(
            os.environ.get(name),
            **cls._kwargs,
        )

        if cls._logger:
            cls._logger(f"Async MongoDB `{name}` instantiated.")

        return client

    def _on_clear(cls, key: str, value: AsyncMongoClient) -> None:
        # Closing is async — use aclear/aclear_all (see _aon_clear).
        pass

    async def _aon_clear(cls, key: str, value: AsyncMongoClient) -> None:
        try:
            await value.close()
        except Exception:
            pass

        if cls._logger:
            cls._logger(f"Async MongoDB `{key}` closed.")


class AsyncMongoHub(metaclass=AsyncMongoHubMeta):
    def __new__(cls, name: str = ""):
        return cls.get(name)
