import logging
import time
import traceback
from typing import Any, Optional

from fun_things.colored_formatter import ColoredFormatter
from fun_things.opentelemetry.otlp_handler import OTLPHandler

try:
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource

except Exception:
    LoggerProvider: Any
    OTLPLogExporter: Any
    BatchLogRecordProcessor: Any
    Resource: Any
    set_logger_provider: Any

    traceback.print_exc()


class OTLPHelper:
    """
    Helper class for managing OpenTelemetry Protocol (OTLP) logging infrastructure.

    Provides a unified interface for logging with both local console output and
    remote OTLP export. Handles initialization, configuration, and lifecycle
    management of OpenTelemetry logging components.

    Attributes:
        project: Project name for resource attributes.
        component: Component name for resource attributes.
        namespace: Service namespace for resource attributes.
        service: Service name for resource attributes.
        version: Service version for resource attributes.
        environment: Deployment environment (e.g., 'production', 'staging').
        otlp_endpoint: HTTP endpoint URL for OTLP log export.
        initialized: Flag indicating whether the helper has been initialized.
    """

    def __init__(
        self,
        *,
        project: str,
        component: str,
        namespace: str,
        service: str,
        version: str,
        environment: str,
        otlp_endpoint: str,
    ):
        """
        Initialize OTLPHelper with service metadata.

        Args:
            project: Project name for resource attributes.
            component: Component name for resource attributes.
            namespace: Service namespace for resource attributes.
            service: Service name for resource attributes.
            version: Service version for resource attributes.
            environment: Deployment environment.
            otlp_endpoint: HTTP endpoint URL for OTLP log export.
        """
        self.project = project
        self.component = component
        self.namespace = namespace
        self.service = service
        self.version = version
        self.environment = environment
        self.otlp_endpoint = otlp_endpoint
        self.initialized = False

    def make_logger_provider(self):
        """
        Create a LoggerProvider with configured resource attributes.

        Returns:
            LoggerProvider: Configured logger provider instance.
        """
        return LoggerProvider(
            resource=self.resource,
        )

    def make_otlp_exporter(self):
        """
        Create an OTLP log exporter for remote log transmission.

        Returns:
            OTLPLogExporter: Configured OTLP exporter instance.
        """
        return OTLPLogExporter(
            endpoint=self.otlp_endpoint,
            headers={},
        )

    def make_batch_processor(self):
        """
        Create a batch log processor for efficient log export.

        Configures batching parameters for optimal performance and resource usage.

        Returns:
            BatchLogRecordProcessor: Configured batch processor instance.
        """
        return BatchLogRecordProcessor(
            self.otlp_exporter,
            schedule_delay_millis=1000,  # Send every 1 second
            max_queue_size=2048,
            max_export_batch_size=512,
        )

    def make_otel_handler(self):
        """
        Create a custom OTLP logging handler with file path information.

        Uses CustomOTLPHandler to include code location attributes
        (file path, line number, function name) in exported logs.
        """
        handler = OTLPHandler(
            logger_provider=self.logger_provider,
        )

        return handler

    def make_direct_logger(self) -> Optional[logging.Logger]:
        """
        Create a logger with both OTLP and console handlers.

        Configures a logger with dual output: colored console output and
        OTLP export. Adds a custom SUCCESS log level (level 25).

        Returns:
            Optional[logging.Logger]: Configured logger instance, or None if creation fails.
        """
        logger = logging.getLogger(f"otlp_direct_{id(self)}")

        logger.setLevel(logging.DEBUG)

        logger.handlers.clear()

        # Add custom SUCCESS level
        logging.addLevelName(25, "SUCCESS")

        logger.addHandler(self.otel_handler)

        console_handler = logging.StreamHandler()

        console_handler.setFormatter(ColoredFormatter.make())
        logger.addHandler(console_handler)

        logger.propagate = False

        return logger

    def initialize(self):
        """
        Initialize the OTLP logging infrastructure.

        Sets up resource attributes, logger provider, OTLP exporter, batch processor,
        and logging handlers. This method is idempotent and can be called multiple times.

        Note:
            If otlp_endpoint is not configured, initialization is skipped.
            If already initialized, subsequent calls have no effect.
        """
        if not self.otlp_endpoint:
            return

        if self.initialized:
            return

        self.initialized = True
        self.resource = Resource.create(
            {
                "service.name": f"{self.namespace}-{self.service}",
                "service.version": self.version,
                "service.namespace": self.namespace,
                "namespace": self.namespace,
                "environment": self.environment,
                "service_name": self.service,
                "project": self.project,
                "component": self.component,
                "telemetry.sdk.language": "python",
                "telemetry.sdk.name": "opentelemetry",
            }
        )

        self.logger_provider = self.make_logger_provider()
        self.otlp_exporter = self.make_otlp_exporter()
        self.batch_processor = self.make_batch_processor()

        self.logger_provider.add_log_record_processor(
            self.batch_processor,
        )
        set_logger_provider(
            self.logger_provider,
        )

        self.otel_handler = self.make_otel_handler()
        self.direct_logger = self.make_direct_logger()

    def flush_logs(
        self,
        timeout_ms: int = 10_000,
    ):
        """
        Force flush of pending log records to the OTLP endpoint.

        Attempts to export all queued log records within the specified timeout,
        with additional time for network transmission.

        Args:
            timeout_ms: Maximum time in milliseconds to wait for flush completion.
                       Defaults to 10,000 (10 seconds).

        Returns:
            bool: True if flush completed successfully, False otherwise.
        """
        if not self.initialized:
            return False

        try:
            success = self.logger_provider.force_flush(
                timeout_ms,
            )

            # Give additional time for network transmission
            time.sleep(1)

            return success
        except Exception:
            return False

    def shutdown(self):
        """
        Shutdown the OTLP logging infrastructure gracefully.

        Flushes pending logs and shuts down the logger provider.
        After shutdown, the helper must be reinitialized before use.

        Returns:
            bool: True if shutdown completed successfully, False otherwise.
        """
        if not self.initialized:
            return False

        self.initialized = False

        try:
            self.flush_logs(
                timeout_ms=5000,
            )

            self.logger_provider.shutdown()

            return True

        except Exception:
            return False

    def log(
        self,
        level: int,
        message: str,
    ):
        """
        Log a message at the specified level.

        Automatically initializes the helper if not already initialized.

        Args:
            level: Logging level (e.g., logging.INFO, logging.ERROR).
            message: Message to log.
        """
        if not self.initialized:
            self.initialize()

        if self.direct_logger is not None:
            self.direct_logger.log(level, message)

    def debug(self, *messages, sep: str = " "):
        """
        Log a debug message.

        Args:
            *messages: Variable number of message components to log.
            sep: Separator string to join message components. Defaults to space.
        """
        self.log(
            logging.DEBUG,
            sep.join(str(msg) for msg in messages),
        )

    def info(self, *messages, sep: str = " "):
        """
        Log an info message.

        Args:
            *messages: Variable number of message components to log.
            sep: Separator string to join message components. Defaults to space.
        """
        self.log(
            logging.INFO,
            sep.join(str(msg) for msg in messages),
        )

    def warning(self, *messages, sep: str = " "):
        """
        Log a warning message.

        Args:
            *messages: Variable number of message components to log.
            sep: Separator string to join message components. Defaults to space.
        """
        self.log(
            logging.WARNING,
            sep.join(str(msg) for msg in messages),
        )

    def error(self, *messages, sep: str = " "):
        """
        Log an error message.

        Args:
            *messages: Variable number of message components to log.
            sep: Separator string to join message components. Defaults to space.
        """
        self.log(
            logging.ERROR,
            sep.join(str(msg) for msg in messages),
        )

    def critical(self, *messages, sep: str = " "):
        """
        Log a critical message.

        Args:
            *messages: Variable number of message components to log.
            sep: Separator string to join message components. Defaults to space.
        """
        self.log(
            logging.CRITICAL,
            sep.join(str(msg) for msg in messages),
        )

    def success(self, *messages, sep: str = " "):
        """
        Log a success message (custom level 25).

        Args:
            *messages: Variable number of message components to log.
            sep: Separator string to join message components. Defaults to space.
        """
        self.log(
            25,
            sep.join(str(msg) for msg in messages),
        )
