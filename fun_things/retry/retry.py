import traceback
from typing import Any, Callable, Generic, NamedTuple, TypeVar, cast
from .retry_response import RetryResponse

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

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        for i in range(1, self.retry_count + 1):
            if i > 1 and self.log:
                print(f"({i}/{self.retry_count}) Retrying...")

            try:
                result = self.callable(*args, **kwargs)

                if self.retry_handler != None and self.retry_handler(result):
                    continue

                return RetryResponse(
                    value=result,
                    ok=True,
                    error=None,  # type: ignore
                )

            except Exception as e:
                if self.log:
                    print(traceback.format_exc())

                ok = True

                if self.error_handler != None:
                    ok = self.error_handler(e)

                if not ok:
                    return RetryResponse(
                        value=cast(T, None),
                        ok=False,
                        error=e,
                    )

        if self.log:
            print(
                f"Failed after retrying {self.retry_count} time(s)!",
            )

        return RetryResponse(
            value=cast(T, None),
            ok=False,
            error=None,  # type: ignore
        )
