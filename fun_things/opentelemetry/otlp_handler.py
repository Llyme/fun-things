import inspect
import json
import logging
import traceback
from typing import Any

from fun_things.frame import get_frame

try:
    from opentelemetry.sdk._logs import LoggingHandler

except Exception:
    LoggingHandler: Any = None

    traceback.print_exc()


class OTLPHandler(LoggingHandler):
    """
    Custom OTLP logging handler that adds file path information to logs.

    Extends the OpenTelemetry LoggingHandler to include code location attributes
    (file path, line number, function name) that will be displayed in Kibana.
    """

    stack_depth = 11

    def __set_caller(self, record: logging.LogRecord):
        """
        Extract actual caller information from the call stack.

        Traverses the call stack to find the actual caller (skipping logging framework frames)
        and returns caller information.

        Returns:
            tuple: (pathname, function_name, line_number) of the actual caller,
                   or (None, None, None) if caller cannot be determined.
        """
        frame = get_frame(self.stack_depth)

        if frame is None:
            return

        frame_info = inspect.getframeinfo(frame)

        pathname = frame_info.filename
        function_name = frame_info.function
        line_number = frame_info.lineno

        setattr(
            record,
            "code.file.path",
            pathname,
        )
        setattr(
            record,
            "code.function.name",
            function_name,
        )
        setattr(
            record,
            "code.line.number",
            line_number,
        )
        setattr(
            record,
            "code.traceback",
            traceback.format_stack(frame),
        )

    def emit(self, record):
        """
        Emit a log record with additional code location attributes.

        Args:
            record: LogRecord instance to emit.
        """
        # Standard attributes that are part of LogRecord
        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "getMessage",
            "exc_info",
            "exc_text",
            "stack_info",
            "message",
            "taskName",
        }

        # Extract any extra fields (anything not in the standard LogRecord attributes)
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_") and "." not in key:
                # Convert complex objects to strings for OTLP compatibility
                if isinstance(value, (dict, list)):
                    setattr(record, key, json.dumps(value))

        self.__set_caller(record)

        # Call parent emit to send to OTLP
        super().emit(record)
