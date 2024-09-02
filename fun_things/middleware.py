from abc import ABC
from signal import SIGABRT, SIGCONT, SIGQUIT
from typing import Generic, List, Type, TypeVar, Union, final
from fun_things import as_asyncgen

T = TypeVar("T", bound="Middleware")
TRetrieve = TypeVar("TRetrieve")


class Middleware(Generic[T], ABC):
    middlewares: List[Type["Middleware"]] = []
    parent: T = None  # type: ignore

    @property
    def root(self):
        return self.__root

    def get_middleware(
        self,
        type: Union[Type[TRetrieve], str],
        recursive: bool = True,
    ) -> TRetrieve:
        middlewares = self.__middleware_instances

        if recursive:
            middlewares = self.__root.__all_middleware_instances

        if isinstance(type, str):
            for key in middlewares:
                if key.__name__ == type:
                    return middlewares[key]

            return None  # type: ignore

        return middlewares.get(type)  # type: ignore

    async def before_run(self):
        pass

    async def after_run(self):
        pass

    @final
    async def run(self):
        if self.parent == None:
            self.__all_middleware_instances: dict = {
                self.__class__: self,
            }
            self.__root = self
        else:
            self.__root = self.parent.__root

        self.__middleware_instances = {}

        # print("START", self.__class__)

        async for result in as_asyncgen(self.before_run()):  # type: ignore
            # print("BEFORE RUN", self.__class__, result)
            if result == None:
                continue

            if result == SIGCONT:
                continue

            if result == SIGABRT:
                return

            if result == SIGQUIT:
                if self.parent != None:
                    yield SIGQUIT

                return

            yield result

        abort = False

        for middleware in self.middlewares:
            instance = middleware()
            self.__middleware_instances[middleware] = instance
            self.__root.__all_middleware_instances[middleware] = instance
            instance.parent = self

            async for result in as_asyncgen(instance.run()):
                # print("MIDDLEWARE", middleware, result)
                if result == None:
                    continue

                if result == SIGCONT:
                    continue

                if result == SIGABRT:
                    abort = True
                    break

                if result == SIGQUIT:
                    abort = True

                    if self.parent != None:
                        yield SIGQUIT

                    break

                yield result

            if abort:
                break

        async for result in as_asyncgen(self.after_run()):  # type: ignore
            # print("AFTER RUN", self.__class__, result)

            if result == None:
                continue

            if result == SIGCONT:
                continue

            if result == SIGABRT:
                return

            if result == SIGQUIT:
                if self.parent != None:
                    yield SIGQUIT

                return

            yield result
