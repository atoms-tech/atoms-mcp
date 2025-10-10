"""Prometheus exporter for metrics.

Based on 2025 Python best practices:
- HTTP endpoint for Prometheus scraping
- Standard /metrics endpoint
- Prometheus text exposition format
- Integration with MetricsCollector
- Support for FastAPI, Flask, and standalone HTTP server
"""

from typing import Callable

from observability.metrics.collector import MetricsCollector


class PrometheusExporter:
    """Prometheus metrics exporter with HTTP endpoint.

    Provides a /metrics endpoint that returns metrics in Prometheus text format
    for scraping by Prometheus server.

    Example:
        >>> from observability.metrics.collector import MetricsCollector
        >>> from observability.exporters.prometheus import PrometheusExporter
        >>>
        >>> collector = MetricsCollector()
        >>> exporter = PrometheusExporter(collector)
        >>>
        >>> # FastAPI integration
        >>> from fastapi import FastAPI, Response
        >>> app = FastAPI()
        >>>
        >>> @app.get("/metrics")
        >>> def metrics():
        ...     return Response(content=exporter.export(), media_type="text/plain")
        >>>
        >>> # Or use the helper
        >>> exporter.setup_fastapi(app)
    """

    def __init__(self, collector: MetricsCollector):
        """Initialize Prometheus exporter.

        Args:
            collector: MetricsCollector instance to export metrics from
        """
        self.collector = collector

    def export(self) -> str:
        """Export metrics in Prometheus text format.

        Returns:
            String containing metrics in Prometheus exposition format
        """
        return self.collector.to_prometheus_text()

    def setup_fastapi(self, app, path: str = "/metrics") -> None:
        """Setup Prometheus metrics endpoint in FastAPI app.

        Args:
            app: FastAPI application instance
            path: URL path for metrics endpoint (default: /metrics)

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> exporter.setup_fastapi(app)
        """
        try:
            from fastapi import Response
        except ImportError:
            raise ImportError("FastAPI is required for setup_fastapi(). Install with: pip install fastapi")

        @app.get(path)
        def metrics_endpoint():
            return Response(content=self.export(), media_type="text/plain; version=0.0.4")

    def setup_flask(self, app, path: str = "/metrics") -> None:
        """Setup Prometheus metrics endpoint in Flask app.

        Args:
            app: Flask application instance
            path: URL path for metrics endpoint (default: /metrics)

        Example:
            >>> from flask import Flask
            >>> app = Flask(__name__)
            >>> exporter.setup_flask(app)
        """
        try:
            from flask import Response
        except ImportError:
            raise ImportError("Flask is required for setup_flask(). Install with: pip install flask")

        @app.route(path)
        def metrics_endpoint():
            return Response(self.export(), mimetype="text/plain; version=0.0.4")

    def create_handler(self) -> Callable:
        """Create a simple HTTP handler function for metrics.

        Returns a function that returns (status_code, headers, body) tuple
        for use with simple HTTP servers.

        Returns:
            Handler function

        Example:
            >>> handler = exporter.create_handler()
            >>> status, headers, body = handler()
        """
        def handler():
            return (
                200,
                {"Content-Type": "text/plain; version=0.0.4"},
                self.export(),
            )

        return handler

    def start_server(self, port: int = 9090, host: str = "0.0.0.0") -> None:
        """Start a standalone HTTP server for metrics endpoint.

        This is useful for applications that don't already have an HTTP server.
        The server runs in a blocking manner.

        Args:
            port: Port to listen on (default: 9090)
            host: Host to bind to (default: 0.0.0.0)

        Example:
            >>> # Run in a separate thread
            >>> import threading
            >>> server_thread = threading.Thread(
            ...     target=lambda: exporter.start_server(port=9090),
            ...     daemon=True
            ... )
            >>> server_thread.start()
        """
        from http.server import BaseHTTPRequestHandler, HTTPServer

        exporter = self

        class MetricsHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/metrics":
                    metrics_text = exporter.export()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; version=0.0.4")
                    self.send_header("Content-Length", str(len(metrics_text)))
                    self.end_headers()
                    self.wfile.write(metrics_text.encode("utf-8"))
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                # Suppress default logging
                pass

        server = HTTPServer((host, port), MetricsHandler)
        print(f"Prometheus metrics server started at http://{host}:{port}/metrics")
        server.serve_forever()
