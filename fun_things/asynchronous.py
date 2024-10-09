import asyncio
import inspect
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Coroutine,
    Generator,
    Iterable,
    Optional,
    TypeVar,
    Union,
)

T1 = TypeVar("T1")
T2 = TypeVar("T2")


def _subdivide_predicate(value):
    if isinstance(value, str):
        return False

    if isinstance(value, bytes):
        return False

    return isinstance(value, Iterable)


async def as_asyncgen(
    value,
    subdivide_predicate: Callable[[Any], bool] = _subdivide_predicate,
):
    """
    Calls a function as an async generator.

    Also awaits async functions.
    """
    if inspect.isasyncgen(value):
        # Already an async generator.
        async for subvalue in value:
            yield subvalue

        return

    if inspect.isawaitable(value):
        value = await value

    if subdivide_predicate(value):
        for subvalue in value:
            yield subvalue

        return

    yield value


async def as_async(
    value: Union[Coroutine[Any, Any, T1], T1],
) -> T1:
    if inspect.isawaitable(value):
        value = await value

    return value  # type: ignore


def as_sync(
    value: Union[Coroutine[Any, Any, T1], T1],
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> T1:
    if inspect.isawaitable(value):
        loop = loop or asyncio.new_event_loop()

        return loop.run_until_complete(value)

    return value


def as_gen(
    value: Union[
        Generator[T1, T2, Any],
        AsyncGenerator[T1, T2],
        Awaitable[T1],
        T1,
    ],
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> Generator[T1, T2, Any]:
    """
    Converts a function into a `Generator`.
    """
    loop = loop or asyncio.new_event_loop()

    if inspect.isawaitable(value):
        value = loop.run_until_complete(value)

    if inspect.isgenerator(value):
        for subvalue in value:
            yield subvalue

        return

    if inspect.isasyncgen(value):
        while True:
            try:
                yield loop.run_until_complete(value.__anext__())

            except StopAsyncIteration:
                return

    yield value  # type: ignore
