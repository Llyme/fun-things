import os
from elasticsearch import Elasticsearch

from .environment_hub import EnvironmentHubMeta


class ElasticsearchHubMeta(EnvironmentHubMeta[Elasticsearch]):
    _formats = EnvironmentHubMeta._bake_basic_uri_formats(
        "ES",
        "ELASTICSEARCH",
    )
    _kwargs: dict = {}

    def _value_selector(cls, name: str):
        return Elasticsearch(
            os.environ.get(name) or "",
            **cls._kwargs,
        )


class ElasticsearchHub(metaclass=ElasticsearchHubMeta):
    def __new__(cls, name: str = ""):
        return cls.get(name)
