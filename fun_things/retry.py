import traceback
from typing import Any, Callable, Generic, NamedTuple, Tuple, TypeVar

T = TypeVar("T")


class Retry(NamedTuple, Generic[T]):
    """
    Allows a callable to be called again if it throws an error.
    """

    callable: Callable[..., T] = None  # type: ignore
    error_handler: Callable[[Exception], bool] = None  # type: ignore
    """
    If the return value is `False`,
    it will stop retrying.
    """
    retry_handler: Callable[[T], bool] = None  # type: ignore
    """
    If return value is `True`,
    it will retry the `callable`.
    """
    retry_count: int = 3
    log: bool = True

    def run(self, *args, **kwargs) -> Tuple[T, bool]:
        for i in range(1, self.retry_count + 1):
            if i > 1 and self.log:
                print(f"({i}/{self.retry_count}) Retrying...")

            try:
                result = self.callable(*args, **kwargs)

                if self.retry_handler != None and self.retry_handler(result):
                    continue

                return result, True

            except Exception as e:
                if self.log:
                    print(traceback.format_exc())

                if self.error_handler != None:
                    if not self.error_handler(e):
                        break

        if self.log:
            print(
                f"Failed after retrying {self.retry_count} time(s)!",
            )

        return None, False  # type: ignore
