from abc import abstractmethod
from datetime import datetime, timedelta
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    final,
)

TArgs = TypeVar("TArgs")
TValue = TypeVar("TValue")


class Cache(Generic[TArgs, TValue]):
    this: "Cache[TArgs, TValue]"

    @property
    def count(self):
        return len(self.cache)

    @property
    def keys(self):
        return self.cache.keys()

    @property
    def values(self):
        return self.cache.values()

    def __init__(self):
        self.cache: Dict[str, Tuple[datetime, TValue]] = {}
        self.lifetime = timedelta(minutes=10)
        self.max_count = 100
        self.logger: Optional[Callable[[str], Any]] = print

    def __getitem__(self, args: TArgs):
        return self.get(args)

    def __setitem__(self, args: TArgs, value: TValue):
        return self.set(args, value)

    @final
    def flush(self):
        now = datetime.now() - self.lifetime
        self.cache = {key: value for key, value in self.cache.items() if value[0] > now}

        if len(self.cache) <= self.max_count:
            return

        # Trim the oldest items until within max_count
        items = sorted(
            self.cache.items(),
            key=lambda x: x[1][0],
            reverse=True,
        )
        self.cache = dict(items[: self.max_count])

    @final
    def flush_all(self):
        self.cache = {}

    @final
    def get(self, args: TArgs):
        key = self._get_key(args)

        if key in self.cache:
            data = self.cache[key][1]

            self.flush()

            return data

        if self.logger:
            self.logger(
                "Loading {} '{}'...".format(
                    self.__class__.__name__,
                    key,
                )
            )

        doc = self._load(args)
        self.cache[key] = (datetime.now(), doc)

        self.flush()

        return doc

    @final
    def set(self, args: TArgs, value: TValue):
        self.cache[self._get_key(args)] = (
            datetime.now(),
            value,
        )

        self.flush()

        return value

    @final
    def get_many(self, argses: Sequence[TArgs]) -> List[TValue]:
        if not argses:
            return []

        missing_indices = []
        result = {}
        missing_args = []
        missing_keys = []
        length = 0

        for index, args in enumerate(argses):
            key = self._get_key(args)
            length += 1

            if key in self.cache:
                result[index] = self.cache[key][1]
            else:
                missing_indices.append(index)
                missing_args.append(args)
                missing_keys.append(key)

        if missing_keys:
            if self.logger:
                self.logger(
                    "Loading {} '{}'...".format(
                        self.__class__.__name__,
                        "', '".join(missing_keys),
                    ),
                )

            docs = self._load_many(missing_args)

            for index, doc in enumerate(docs):
                result[missing_indices[index]] = doc
                self.cache[missing_keys[index]] = (
                    datetime.now(),
                    doc,
                )

        self.flush()

        return [result[i] for i in range(length)]

    @abstractmethod
    def _get_key(self, args: TArgs) -> str:
        raise NotImplementedError("Not implemented")

    def _load(self, args: TArgs) -> TValue:
        raise NotImplementedError("Not implemented")

    def _load_many(self, argses: List[TArgs]) -> List[TValue]:
        raise NotImplementedError("Not implemented")
