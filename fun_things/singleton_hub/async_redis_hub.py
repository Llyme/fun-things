import os

from redis.asyncio import Redis

from . import AsyncSingletonHubMeta
from .environment_hub import EnvironmentHubMeta


class AsyncRedisHubMeta(
    EnvironmentHubMeta[Redis],
    AsyncSingletonHubMeta[Redis],
):
    """Async counterpart of :class:`RedisHubMeta`.

    Builds ``redis.asyncio`` clients. The accessor is synchronous; only the
    operations are awaited. Closing is a coroutine, so teardown is the async
    ``aclear`` / ``aclear_all`` (which close *and* clear the cache) — awaited
    inside the running event loop.
    """

    _formats = EnvironmentHubMeta._bake_basic_uri_formats(
        "REDIS",
    )
    _kwargs: dict = {}
    _log: bool = True

    def _value_selector(cls, name: str):
        client = Redis.from_url(
            os.environ.get(name) or "",
            **cls._kwargs,
        )

        if cls._log:
            print(f"Async Redis `{name}` instantiated.")

        return client

    def _on_clear(cls, key: str, value: Redis) -> None:
        # Closing is async — use aclear/aclear_all (see _aon_clear).
        pass

    async def _aon_clear(cls, key: str, value: Redis) -> None:
        try:
            await value.aclose()
        except Exception:
            pass

        if cls._log:
            print(f"Async Redis `{key}` closed.")


class AsyncRedisHub(metaclass=AsyncRedisHubMeta):
    def __new__(cls, name: str = ""):
        return cls.get(name)
