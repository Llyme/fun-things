from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar, final

T = TypeVar("T")


class SingletonFactory(Generic[T], ABC):
    """
    Abstract base class implementing the Singleton-Factory design pattern.

    Ensures that only one instance of a class is created, and provides methods for
    destroying the instance and keeping track of all instances.

    Subclasses must implement the `_instantiate` and `_destroy` abstract methods.
    """

    __all: List["SingletonFactory"] = []

    __instantiated: bool = False
    __instance: T

    @property
    def instance(self):
        """
        Returns the instance of the Singleton class.

        The instance is created on first invocation and
        remains the same for all subsequent invocations.

        :return: The instance of the Singleton class
        :rtype: T
        """
        return self()

    @property
    def kwargs(self):
        return self.__kwargs

    @property
    def args(self):
        return self.__args

    def __init__(self, *args, **kwargs):
        self.__kwargs = kwargs
        self.__args = args

        SingletonFactory.__all.append(self)

    def __call__(self):
        """
        Returns the instance of the Singleton class.

        The instance is created on first invocation and
        remains the same for all subsequent invocations.

        :return: The instance of the Singleton class
        :rtype: T
        """
        if not self.__instantiated:
            self.__instance = self._instantiate()
            self.__instantiated = True

        return self.__instance

    @abstractmethod
    def _instantiate(self) -> T:
        """
        Instantiates the Singleton class.

        This method is called when the instance is first requested.
        It should create and return the instance of the Singleton class.

        :return: The instance of the Singleton class
        :rtype: T
        """
        pass

    @abstractmethod
    def _destroy(self) -> bool:
        """
        Destroys the instance of the Singleton class.

        This method is called when the `destroy` method is invoked.
        It should destroy the instance of the Singleton class and
        return `True` if the destruction was successful.

        :return: `True` if the instance was destroyed.
        :rtype: bool
        """
        pass

    @final
    def destroy(self):
        """
        Destroys the instance of the Singleton class.

        :return: `True` if the instance was destroyed.
        :rtype: bool
        """
        if not self.__instantiated:
            return False

        ok = self._destroy()

        if ok:
            self.__instantiated = False

        return ok

    @final
    @classmethod
    def all(cls):
        """
        Yields all instances of the Singleton class.

        This method is a generator function which yields all instances
        of the Singleton class. The order in which the instances are
        returned is not guaranteed.

        :return: A generator of all instances of the Singleton class
        :rtype: Iterator[T]
        """
        for instance in cls.__all:
            yield instance

    @final
    @classmethod
    def destroy_all(cls):
        """
        Destroys all instances of the Singleton class.

        Iterates over all stored instances and calls their `destroy` method.
        Returns the count of instances that were successfully destroyed.

        :return: The number of instances destroyed
        :rtype: int
        """
        n = 0

        for conn in cls.__all:
            if conn.destroy():
                n += 1

        return n
