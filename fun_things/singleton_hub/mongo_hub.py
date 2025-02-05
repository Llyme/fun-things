import os
from pymongo import MongoClient

from .environment_hub import EnvironmentHubMeta


class MongoHubMeta(EnvironmentHubMeta[MongoClient]):
    _formats = EnvironmentHubMeta._bake_basic_uri_formats(
        "MONGO",
        "MONGO_DB",
    )
    _kwargs: dict = {}

    def _value_selector(cls, name: str):
        return MongoClient(
            os.environ.get(name),
            **cls._kwargs,
        )


class MongoHub(metaclass=MongoHubMeta):
    def __new__(cls, name: str = ""):
        return cls.get(name)
