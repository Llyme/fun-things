from abc import ABC
import asyncio
from signal import SIGABRT, SIGCONT, SIGQUIT
from typing import (
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    final,
)
from fun_things import as_asyncgen, as_gen

TParent = TypeVar("TParent", bound="Middleware")
TChild = TypeVar("TChild", bound="Middleware")


class Middleware(Generic[TParent], ABC):
    PRIORITY: int = 0
    MIDDLEWARES: List[Type["Middleware"]] = []
    """
    Nested middlewares.
    """
    parent: TParent = None  # type: ignore

    __middleware_instances: Dict[
        Type["Middleware"],
        "Middleware",
    ]
    __all_middleware_instances: Dict[
        Type["Middleware"],
        "Middleware",
    ]

    @property
    def root(self):
        return self.__root

    def get_middleware(
        self,
        type: Union[Type[TChild], str],
        recursive: bool = True,
    ) -> TChild:
        middlewares = self.__middleware_instances

        if recursive:
            middlewares = self.__root.__all_middleware_instances

        if isinstance(type, str):
            for key in middlewares:
                if key.__name__ == type:
                    return middlewares[key]  # type: ignore

            return None  # type: ignore

        return middlewares.get(type)  # type: ignore

    def before_run(self):
        """
        Called before the nested middlewares are called.

        Can be asynchronous.
        """
        pass

    def after_run(self):
        """
        Called after the nested middlewares are called.

        Can be asynchronous.
        """
        pass

    @final
    def __instantiate(self, middleware: Type[TChild]):
        instance = middleware()
        self.__middleware_instances[middleware] = instance
        self.__root.__all_middleware_instances[middleware] = instance
        instance.parent = self

        return instance

    @final
    def __build_annotations(self):
        if "__annotations__" not in self.__class__.__dict__:
            return

        annotations = self.__class__.__annotations__

        for key, type in annotations.items():
            if not issubclass(type, Middleware):
                continue

            setattr(self, key, self.__instantiate(type))

    @final
    def run_all(
        self,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        return [*self.run(loop)]

    @final
    def run(
        self,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        return as_gen(self.run_async(), loop)

    @final
    async def run_all_async(self):
        results = []

        async for result in self.run_async():
            results.append(result)

        return results

    @final
    async def run_async(self):
        if self.parent == None:
            self.__all_middleware_instances = {
                self.__class__: self,
            }
            self.__root = self
        else:
            self.__root = self.parent.__root

        self.__middleware_instances = {}

        self.__build_annotations()

        for middleware in self.MIDDLEWARES:
            self.__instantiate(middleware)

        async for item in as_asyncgen(self.before_run()):
            # print("BEFORE RUN", self.__class__, result)

            if item == SIGCONT:
                continue

            if item == SIGABRT:
                return

            if item == SIGQUIT:
                if self.parent != None:
                    yield SIGQUIT

                return

        # print("START", self.__class__)

        middlewares = sorted(
            self.__middleware_instances.values(),
            key=lambda middleware: middleware.PRIORITY,
            reverse=True,
        )
        abort = False

        for middleware in middlewares:
            async for item in as_asyncgen(middleware.run_async()):
                # print("MIDDLEWARE", middleware, result)
                if item == SIGCONT:
                    continue

                if item == SIGABRT:
                    abort = True
                    break

                if item == SIGQUIT:
                    abort = True

                    if self.parent != None:
                        yield SIGQUIT

                    break

            if abort:
                break

        async for item in as_asyncgen(self.after_run()):
            # print("AFTER RUN", self.__class__, result)
            if item == SIGCONT:
                continue

            if item == SIGABRT:
                return

            if item == SIGQUIT:
                if self.parent != None:
                    yield SIGQUIT

                return
