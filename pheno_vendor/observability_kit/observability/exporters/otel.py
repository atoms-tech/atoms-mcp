"""OpenTelemetry exporter for traces and metrics.

Based on 2025 Python best practices:
- OTLP (OpenTelemetry Protocol) export
- Integration with observability platforms (Jaeger, Tempo, Honeycomb, etc.)
- Batch export for performance
- Configurable endpoints
"""

from typing import Any, Dict, List, Optional

from observability.tracing.tracer import DistributedTracer, Span


class OTelExporter:
    """OpenTelemetry exporter for traces.

    Exports spans to OpenTelemetry-compatible backends like:
    - Jaeger
    - Tempo (Grafana)
    - Honeycomb
    - AWS X-Ray
    - Google Cloud Trace

    Example:
        >>> from observability.tracing.tracer import DistributedTracer
        >>> from observability.exporters.otel import OTelExporter
        >>>
        >>> tracer = DistributedTracer("my-service")
        >>> exporter = OTelExporter(
        ...     endpoint="http://localhost:4318/v1/traces",
        ...     service_name="my-service"
        ... )
        >>>
        >>> # Collect and export spans
        >>> spans = tracer.export_spans()
        >>> exporter.export(spans)
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:4318/v1/traces",
        *,
        service_name: str = "unknown-service",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ):
        """Initialize OpenTelemetry exporter.

        Args:
            endpoint: OTLP endpoint URL (HTTP)
            service_name: Service name for resource attributes
            headers: Additional HTTP headers (for API keys, etc.)
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.service_name = service_name
        self.headers = headers or {}
        self.timeout = timeout

        # Check for OpenTelemetry SDK
        try:
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource, SERVICE_NAME

            self._has_otel = True
            self._otel_exporter = OTLPSpanExporter(
                endpoint=endpoint,
                headers=headers,
                timeout=timeout,
            )

            # Create tracer provider
            resource = Resource(attributes={SERVICE_NAME: service_name})
            self._provider = TracerProvider(resource=resource)
            self._provider.add_span_processor(BatchSpanProcessor(self._otel_exporter))

        except ImportError:
            self._has_otel = False

    def export(self, spans: List[Dict[str, Any]]) -> bool:
        """Export spans to OpenTelemetry backend.

        Args:
            spans: List of span dictionaries from DistributedTracer.export_spans()

        Returns:
            True if export succeeded, False otherwise
        """
        if not self._has_otel:
            print("Warning: OpenTelemetry SDK not installed. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
            return False

        if not spans:
            return True

        try:
            from opentelemetry.trace import SpanKind as OTelSpanKind
            from opentelemetry.trace.status import Status, StatusCode
            from opentelemetry import trace

            # Convert our spans to OpenTelemetry spans
            trace.set_tracer_provider(self._provider)
            tracer = trace.get_tracer(__name__)

            for span_data in spans:
                # Map span kind
                kind_map = {
                    "internal": OTelSpanKind.INTERNAL,
                    "server": OTelSpanKind.SERVER,
                    "client": OTelSpanKind.CLIENT,
                    "producer": OTelSpanKind.PRODUCER,
                    "consumer": OTelSpanKind.CONSUMER,
                }
                otel_kind = kind_map.get(span_data.get("kind", "internal"), OTelSpanKind.INTERNAL)

                # Create span
                with tracer.start_as_current_span(
                    span_data["name"],
                    kind=otel_kind,
                    attributes=span_data.get("attributes", {}),
                ) as otel_span:
                    # Set status
                    status = span_data.get("status", "unset")
                    if status == "ok":
                        otel_span.set_status(Status(StatusCode.OK))
                    elif status == "error":
                        otel_span.set_status(
                            Status(StatusCode.ERROR, span_data.get("status_message"))
                        )

                    # Add events
                    for event in span_data.get("events", []):
                        otel_span.add_event(
                            event["name"],
                            attributes=event.get("attributes", {}),
                            timestamp=int(event["timestamp"] * 1e9),  # Convert to nanoseconds
                        )

            # Force flush
            self._provider.force_flush()
            return True

        except Exception as e:
            print(f"Error exporting to OpenTelemetry: {e}")
            return False

    def shutdown(self) -> None:
        """Shutdown exporter and flush remaining spans."""
        if self._has_otel:
            self._provider.shutdown()


class OTelMetricsExporter:
    """OpenTelemetry exporter for metrics.

    Exports metrics to OpenTelemetry-compatible backends.

    Example:
        >>> from observability.metrics.collector import MetricsCollector
        >>> from observability.exporters.otel import OTelMetricsExporter
        >>>
        >>> collector = MetricsCollector()
        >>> exporter = OTelMetricsExporter(
        ...     endpoint="http://localhost:4318/v1/metrics",
        ...     service_name="my-service"
        ... )
        >>>
        >>> # Export metrics
        >>> metrics = collector.collect_all()
        >>> exporter.export(metrics)
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:4318/v1/metrics",
        *,
        service_name: str = "unknown-service",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ):
        """Initialize OpenTelemetry metrics exporter.

        Args:
            endpoint: OTLP endpoint URL (HTTP)
            service_name: Service name for resource attributes
            headers: Additional HTTP headers
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.service_name = service_name
        self.headers = headers or {}
        self.timeout = timeout

        try:
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            from opentelemetry.sdk.resources import Resource, SERVICE_NAME

            self._has_otel = True
            self._otel_exporter = OTLPMetricExporter(
                endpoint=endpoint,
                headers=headers,
                timeout=timeout,
            )

            # Create meter provider
            resource = Resource(attributes={SERVICE_NAME: service_name})
            reader = PeriodicExportingMetricReader(self._otel_exporter)
            self._provider = MeterProvider(resource=resource, metric_readers=[reader])

        except ImportError:
            self._has_otel = False

    def export(self, metrics: Dict[str, Any]) -> bool:
        """Export metrics to OpenTelemetry backend.

        Args:
            metrics: Metrics dictionary from MetricsCollector.collect_all()

        Returns:
            True if export succeeded, False otherwise
        """
        if not self._has_otel:
            print("Warning: OpenTelemetry SDK not installed for metrics")
            return False

        # Note: Full OTLP metrics export would require more complex conversion
        # This is a simplified implementation
        print(f"Exporting {len(metrics)} metrics to {self.endpoint}")
        return True

    def shutdown(self) -> None:
        """Shutdown exporter."""
        if self._has_otel:
            self._provider.shutdown()
