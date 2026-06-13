import json
import logging
import traceback
from typing import Any

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

    def __set_caller(self, record: logging.LogRecord):
        """
        Attach code-location attributes for OTLP export.

        Uses the caller info already on the record (set by ``logging``'s
        ``findCaller`` or by ``OTLPHelper.log`` from the real frame) rather than
        re-walking the stack at a fixed depth — a fixed depth points at the wrong
        frame the moment the call passes through wrapper layers (e.g. a project's
        ``say()``/``discord`` helpers).
        """

        setattr(record, "code.file.path", record.pathname)
        setattr(record, "code.function.name", record.funcName)
        setattr(record, "code.line.number", record.lineno)

        if record.stack_info:
            setattr(record, "code.traceback", record.stack_info)

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
