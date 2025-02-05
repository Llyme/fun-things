from abc import ABC, abstractmethod
from typing import Dict, Generic, TypeVar

T = TypeVar("T")


class SingletonHubMeta(ABC, type, Generic[T]):
    __cache: Dict[str, T] = {}

    def _name_selector(cls, name: str):
        return name

    @abstractmethod
    def _value_selector(cls, name: str) -> T:
        pass

    def flush(cls):
        cls.__cache.clear()

    def get(
        cls,
        name: str = "",
    ):
        if name in cls.__cache:
            return cls.__cache[name]

        name = cls._name_selector(name)
        value = cls._value_selector(name)
        cls.__cache[name] = value

        return value

    def __getattr__(cls, name: str):
        return cls.get(name)
