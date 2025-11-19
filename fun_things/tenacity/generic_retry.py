import traceback
from typing import Any, Callable, Optional, Union

from tenacity import (
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

try:
    import tenacity

except Exception:
    tenacity = None


def generic_retry_error_callback(
    *,
    retry_state: RetryCallState,
    error_logger: Optional[Callable[[str], Any]] = print,
    reraise: bool = True,
):
    outcome = retry_state.outcome

    if not outcome:
        return

    e = outcome.exception()

    if not e:
        return

    if error_logger:
        error_logger("".join(traceback.format_exception(e)))

    if reraise:
        raise e


def generic_retry(
    *,
    stop=stop_after_attempt(3),
    wait=wait_exponential(),
    retry: Any = retry_if_exception_type(),
    retry_message: Union[
        str, Callable[[RetryCallState], str]
    ] = lambda retry_state: f"#{retry_state.attempt_number} Retrying in {retry_state.upcoming_sleep:.2f}s...",
    reraise=True,
    warning_logger: Optional[Callable[[str], Any]] = print,
    error_logger: Optional[Callable[[str], Any]] = print,
):
    if tenacity is None:
        raise ImportError("tenacity is not installed")

    return tenacity.retry(
        stop=stop,
        wait=wait,
        reraise=reraise,
        retry=retry,
        before_sleep=lambda retry_state: print(
            retry_message(retry_state) if callable(retry_message) else retry_message
        )
        if warning_logger and retry_state.attempt_number < stop.max_attempt_number
        else None,
        retry_error_callback=lambda retry_state: generic_retry_error_callback(
            retry_state=retry_state,
            error_logger=error_logger,
            reraise=reraise,
        ),
    )
