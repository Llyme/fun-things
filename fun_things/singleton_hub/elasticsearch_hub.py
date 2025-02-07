import os
import re
from elasticsearch import Elasticsearch

from .environment_hub import EnvironmentHubMeta


class ElasticsearchHubMeta(EnvironmentHubMeta[Elasticsearch]):
    _formats = EnvironmentHubMeta._bake_basic_uri_formats(
        "ES",
        "ELASTICSEARCH",
        formats=[
            *EnvironmentHubMeta._DEFAULT_FORMATS,
            "{keyword}_URIS",
            "{keyword}_URLS",
            "{keyword}_CONNECTION_URIS",
            "{keyword}_CONNECTION_URLS",
            "{keyword}_CONNECTION_STRINGS",
            "{{name}}_{keyword}_URIS",
            "{{name}}_{keyword}_URLS",
            "{{name}}_{keyword}_CONNECTION_URIS",
            "{{name}}_{keyword}_CONNECTION_URLS",
            "{{name}}_{keyword}_CONNECTION_STRINGS",
            "{keyword}_{{name}}",
            "{keyword}_URIS_{{name}}",
            "{keyword}_URLS_{{name}}",
            "{keyword}_CONNECTION_URIS_{{name}}",
            "{keyword}_CONNECTION_URLS_{{name}}",
            "{keyword}_CONNECTION_STRINGS_{{name}}",
        ],
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
