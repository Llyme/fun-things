from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class lazy(Generic[T]):
    def __init__(
        self,
        fn: Callable[..., T],
    ) -> None:
        self.__fn = fn
        self.__instance: T = None  # type: ignore
        self.__exists: bool = False

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = self.__fn(instance)

        setattr(
            instance,
            self.__fn.__name__,
            value,
        )

        return value

    def __call__(
        self,
        *args,
        **kwargs,
    ):
        if not self.__exists:
            self.__exists = True
            self.__instance = self.__fn(
                *args,
                **kwargs,
            )

        return self.__instance

    @property
    def self(self):
        return self.__instance

    @property
    def exists(self):
        return self.__exists

    def clear(self):
        self.__exists = False
        self.__instance = None  # type: ignore
