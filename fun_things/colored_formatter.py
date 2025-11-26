import inspect
import logging

from fun_things.frame import get_frame


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

    stack_depth = 13

    @property
    def traceback(self):
        """
        Extract caller information from the call stack.

        Traverses the call stack to find the actual caller (skipping logging framework frames)
        and returns formatted caller information.

        Returns:
            str: Formatted string containing module, function, and line number of the caller,
                 or empty string if caller information cannot be determined.
        """
        frame = get_frame(self.stack_depth)

        if frame is None:
            return ""

        frame_info = inspect.getframeinfo(frame)
        frame_module = inspect.getmodule(frame)
        module_name = frame_module.__name__ if frame_module else ""
        caller_module = module_name
        caller_funcName = frame_info.function
        caller_lineno = frame_info.lineno

        return f"{caller_module}:{caller_funcName}:{caller_lineno} -"

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
            traceback=self.traceback,
            message=record.getMessage(),
        )

        return formatted

    @classmethod
    def make(cls):
        """
        Create a new `ColoredFormatter` instance with default date format.

        Returns:
            ColoredFormatter: New formatter instance configured with ISO-style datetime format.
        """
        return ColoredFormatter(
            datefmt="%Y-%m-%d %H:%M:%S",
        )
