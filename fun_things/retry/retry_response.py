from typing import Generic, NamedTuple, TypeVar

TValue = TypeVar("TValue")


class RetryResponse(Generic[TValue], NamedTuple):
    value: TValue
    ok: bool
    error: Exception
