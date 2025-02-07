import os
import re
from elasticsearch import Elasticsearch

from .environment_hub import EnvironmentHubMeta


class ElasticsearchHubMeta(EnvironmentHubMeta[Elasticsearch]):
    _formats = EnvironmentHubMeta._bake_basic_uri_formats(
        "ES",
        "ELASTICSEARCH",
    )
    _kwargs: dict = {}
    _log: bool = True

    def _value_selector(cls, name: str):
        client = Elasticsearch(
            [
                clean_uri
                for uri in re.compile(r",|\n").split(
                    os.environ.get(name) or "",
                )
                if (clean_uri := uri.strip())
            ],
            **cls._kwargs,
        )

        if cls._log:
            print(f"Elasticsearch `{name}` connected.")

        return client

    def _on_clear(
        cls,
        key: str,
        value: Elasticsearch,
    ) -> None:
        value.close()

        if cls._log:
            print(f"Elasticsearch `{key}` closed.")


class ElasticsearchHub(metaclass=ElasticsearchHubMeta):
    def __new__(cls, name: str = ""):
        return cls.get(name)
