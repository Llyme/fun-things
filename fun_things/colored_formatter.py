import logging
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter with ANSI color codes for console output.

    Provides colored log output with timestamps, log levels, and caller information.
    Supports standard log levels plus a custom SUCCESS level.

    Attributes:
        COLORS: Dictionary mapping log level names to ANSI color codes.
        RESET: ANSI code to reset color formatting.
        GRAY: ANSI code for gray color.
        FORMAT: Format string template for log messages.
        STACK_DEPTH: Number of stack frames to traverse to find the actual caller.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[90m",  # Gray
        "INFO": "\033[97m",  # White
        "WARNING": "\033[93m",  # Bright Yellow
        "ERROR": "\033[91m",  # Bright Red
        "CRITICAL": "\033[1;91m",  # Bright Bold Red
        "SUCCESS": "\033[92m",  # Bright Green
    }
    RESET = "\033[0m"
    GRAY = "\033[90m"
    FORMAT = f"{GRAY}{{time}}{RESET} | {{level_color}}{{level:<8}}{RESET} | {GRAY}{{traceback}}{RESET} {{level_color}}{{message}}{RESET}"

    @staticmethod
    def _caller(record: logging.LogRecord) -> str:
        """Caller info straight off the record (set by logging or the caller).

        Uses the record's own ``module``/``funcName``/``lineno`` rather than
        re-walking the stack at a fixed depth — a fixed depth points at the
        wrong frame as soon as the call goes through wrapper layers.
        """

        return f"{record.module}:{record.funcName}:{record.lineno} -"

    def format(self, record):
        """
        Format a log record with colors and caller information.

        Args:
            record: LogRecord instance to format.

        Returns:
            str: Formatted log message with ANSI color codes.
        """
        color = self.COLORS.get(
            record.levelname,
            "",
        )

        asctime = self.formatTime(record, self.datefmt)

        formatted = self.FORMAT.format(
            time=asctime,
            level_color=color,
            level=record.levelname,
            traceback=self._caller(record),
            message=super().format(record),
        )

        return formatted

    @classmethod
    def make(
        cls,
        *,
        fmt: Optional[str] = None,
    ):
        """
        Create a new `ColoredFormatter` instance with default date format.

        Returns:
            ColoredFormatter: New formatter instance configured with ISO-style datetime format.
        """
        return ColoredFormatter(
            fmt=fmt,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
