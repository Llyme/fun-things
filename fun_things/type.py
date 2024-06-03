from typing import Any, Generator, Type, TypeVar

T = TypeVar("T", bound=Type)


def get_all_descendant_classes(cls: T) -> Generator[T, Any, None]:
    """
    Returns all direct and non-direct subclasses.
    """
    queue = [cls]
    subclasses = cls.__subclasses__()

    while len(queue) > 0:
        subclasses = queue.pop().__subclasses__()

        for subclass in subclasses:
            yield subclass

            queue.append(subclass)
