import asyncio
import inspect
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Generator,
    Iterable,
    Optional,
    TypeVar,
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


async def as_async(value):
    if inspect.isawaitable(value):
        value = await value

    return value


def as_gen(
    values: AsyncGenerator[T1, T2],
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> Generator[T1, T2, None]:
    """
    Converts an async generator to a non-async generator.
    """
    loop = loop or asyncio.get_event_loop()

    while True:
        try:
            yield loop.run_until_complete(
                values.__anext__(),
            )

        except StopAsyncIteration:
            break
