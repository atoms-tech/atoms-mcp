"""
WebSocket streaming for real-time dashboard updates.

Provides WebSocket server for streaming dashboard data to clients.
Requires websockets package (optional dependency).
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WebSocketServerProtocol = None
    WEBSOCKETS_AVAILABLE = False

from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class DashboardStreamer:
    """
    Streams dashboard data to WebSocket clients.

    Provides real-time updates for:
    - Metric updates
    - Health status changes
    - Alert notifications
    - System events

    Example:
        streamer = DashboardStreamer(dashboard_collector)
        await streamer.start(port=8765)

        # Broadcast an update
        await streamer.broadcast({
            "type": "metric_update",
            "data": {"name": "api_requests", "value": 100}
        })
    """

    def __init__(
        self,
        dashboard_collector=None,
        port: int = 8765,
        host: str = "localhost",
    ):
        """
        Initialize dashboard streamer.

        Args:
            dashboard_collector: DashboardDataCollector instance
            port: WebSocket server port
            host: WebSocket server host
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets package is required for streaming. "
                "Install with: pip install websockets"
            )

        self.dashboard_collector = dashboard_collector
        self.port = port
        self.host = host
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        self._server_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the WebSocket server."""
        try:
            self.server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port,
            )
            logger.info(f"Dashboard WebSocket server started on {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Close all client connections
        if self.connected_clients:
            await asyncio.gather(
                *[client.close() for client in self.connected_clients],
                return_exceptions=True,
            )
            self.connected_clients.clear()

        logger.info("Dashboard WebSocket server stopped")

    async def _handle_client(
        self,
        websocket: WebSocketServerProtocol,
        path: str,
    ) -> None:
        """Handle a WebSocket client connection."""
        logger.info(f"New WebSocket client connected from {websocket.remote_address}")
        self.connected_clients.add(websocket)

        try:
            # Send initial dashboard data
            if self.dashboard_collector:
                dashboard_data = await self.dashboard_collector.get_dashboard_data()
                await websocket.send(
                    json.dumps({
                        "type": "dashboard_data",
                        "data": dashboard_data,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                )

            # Handle incoming messages
            async for message in websocket:
                try:
                    request = json.loads(message)
                    await self._handle_client_request(websocket, request)
                except json.JSONDecodeError:
                    await websocket.send(
                        json.dumps({
                            "type": "error",
                            "message": "Invalid JSON",
                        })
                    )
                except Exception as e:
                    logger.error(f"Error handling client request: {e}")
                    await websocket.send(
                        json.dumps({
                            "type": "error",
                            "message": str(e),
                        })
                    )

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.connected_clients.discard(websocket)

    async def _handle_client_request(
        self,
        websocket: WebSocketServerProtocol,
        request: Dict[str, Any],
    ) -> None:
        """Handle a specific client request."""
        request_type = request.get("type")

        if request_type == "get_dashboard":
            if self.dashboard_collector:
                time_range = request.get("time_range_minutes", 30)
                tenant_id = request.get("tenant_id")

                dashboard_data = await self.dashboard_collector.get_dashboard_data(
                    time_range_minutes=time_range,
                    tenant_id=tenant_id,
                )

                await websocket.send(
                    json.dumps({
                        "type": "dashboard_data",
                        "data": dashboard_data,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                )

        elif request_type == "subscribe":
            # Client wants to subscribe to specific events
            event_types = request.get("events", [])
            await websocket.send(
                json.dumps({
                    "type": "subscribed",
                    "events": event_types,
                })
            )

        elif request_type == "ping":
            await websocket.send(
                json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            )

    async def broadcast(
        self,
        message: Dict[str, Any],
        filter_func=None,
    ) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message dictionary to broadcast
            filter_func: Optional function to filter clients
        """
        if not self.connected_clients:
            return

        message_str = json.dumps(message)
        disconnected_clients = set()

        clients_to_notify = (
            [c for c in self.connected_clients if filter_func(c)]
            if filter_func
            else self.connected_clients
        )

        for client in clients_to_notify:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.debug(f"Failed to send message to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.connected_clients -= disconnected_clients

    async def broadcast_metric(
        self,
        name: str,
        value: float,
        metric_type: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Broadcast a metric update to all clients."""
        await self.broadcast({
            "type": "metric_update",
            "data": {
                "name": name,
                "value": value,
                "type": metric_type,
                "labels": labels or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })

    async def broadcast_health_update(self, health_data: Dict[str, Any]) -> None:
        """Broadcast a health status update."""
        await self.broadcast({
            "type": "health_update",
            "data": health_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def broadcast_alert(
        self,
        alert_type: str,
        alert_data: Dict[str, Any],
    ) -> None:
        """Broadcast an alert notification."""
        await self.broadcast({
            "type": "alert",
            "alert_type": alert_type,
            "data": alert_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


class WebSocketDashboard:
    """
    Complete WebSocket-based dashboard with automatic updates.

    Combines streaming, data collection, and periodic updates.
    """

    def __init__(
        self,
        dashboard_collector,
        port: int = 8765,
        host: str = "localhost",
        update_interval_seconds: int = 5,
    ):
        """
        Initialize WebSocket dashboard.

        Args:
            dashboard_collector: DashboardDataCollector instance
            port: WebSocket server port
            host: WebSocket server host
            update_interval_seconds: How often to push updates
        """
        self.streamer = DashboardStreamer(dashboard_collector, port, host)
        self.update_interval = update_interval_seconds
        self._update_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the dashboard server and update loop."""
        await self.streamer.start()
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("WebSocket dashboard started")

    async def stop(self) -> None:
        """Stop the dashboard server."""
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        await self.streamer.stop()
        logger.info("WebSocket dashboard stopped")

    async def _update_loop(self) -> None:
        """Periodically push dashboard updates to clients."""
        while True:
            try:
                await asyncio.sleep(self.update_interval)

                if not self.streamer.connected_clients:
                    continue

                # Get fresh dashboard data
                dashboard_data = await self.streamer.dashboard_collector.get_dashboard_data()

                # Broadcast to all clients
                await self.streamer.broadcast({
                    "type": "dashboard_update",
                    "data": dashboard_data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                await asyncio.sleep(self.update_interval)


# Global streamer instance
_dashboard_streamer: Optional[DashboardStreamer] = None


def get_dashboard_streamer() -> DashboardStreamer:
    """Get the global dashboard streamer instance."""
    global _dashboard_streamer
    if _dashboard_streamer is None:
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets package is required. "
                "Install with: pip install websockets"
            )
        _dashboard_streamer = DashboardStreamer()
    return _dashboard_streamer
