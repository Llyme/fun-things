import os

from redis.asyncio import Redis

from .environment_hub import EnvironmentHubMeta


class AsyncRedisHubMeta(EnvironmentHubMeta[Redis]):
    """Async counterpart of :class:`RedisHubMeta`.

    Builds ``redis.asyncio`` clients. The accessor is synchronous; only the
    operations are awaited. Closing is a coroutine, so teardown is
    :meth:`aclose_all` (an awaitable) — it must be awaited inside the running
    event loop.
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
        # Closing is async — handled in aclose_all, not here.
        pass

    async def aclose_all(cls):
        """Awaitable cleanup — close every cached client.

        ``clear_all`` drops the cache and returns the clients (its ``_on_clear``
        is a no-op here), which are then closed with ``await``.
        """
        for key, value in cls.clear_all().items():
            try:
                await value.aclose()
            except Exception:
                pass

            if cls._log:
                print(f"Async Redis `{key}` closed.")


class AsyncRedisHub(metaclass=AsyncRedisHubMeta):
    def __new__(cls, name: str = ""):
        return cls.get(name)
