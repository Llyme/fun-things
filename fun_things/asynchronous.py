import inspect
from typing import Any, Callable, Iterable


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
