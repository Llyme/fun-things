import os
from redis import Redis

from .environment_hub import EnvironmentHubMeta


class RedisHubMeta(EnvironmentHubMeta[Redis]):
    _formats = EnvironmentHubMeta._bake_basic_uri_formats(
        "REDIS",
    )
    _kwargs: dict = {}

    def _value_selector(cls, name: str):
        return Redis.from_url(
            os.environ.get(name) or "",
            **cls._kwargs,
        )


class RedisHub(metaclass=RedisHubMeta):
    def __new__(cls, name: str = ""):
        return cls.get(name)
