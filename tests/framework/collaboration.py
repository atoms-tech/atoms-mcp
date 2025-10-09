"""Collaboration helpers built on event-kit and workflow-kit."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Optional

from event_kit.core.event_bus import Event, EventBus
from workflow_kit.task import Worker, task

TEST_EVENT_CHANNEL = "atoms.tests.events"


@dataclass
class TestEvent:
    """Simplified collaboration event payload."""

    event_type: str
    test_name: str
    endpoint: str
    user: str
    data: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()

    def to_bus_event(self) -> Event:
        return Event(name=TEST_EVENT_CHANNEL, data=asdict(self))

    @classmethod
    def from_event(cls, event: Event) -> "TestEvent":
        payload = dict(event.data)
        payload.setdefault("timestamp", event.timestamp)
        return cls(**payload)


class CollaborationFactory:
    """Factory creating event-driven collaboration helpers."""

    def __init__(self, bus: Optional[EventBus] = None, worker: Optional[Worker] = None):
        self.bus = bus or EventBus()
        self.worker = worker or Worker(concurrency=4)

    def create_broadcaster(self) -> "CollaborationBroadcaster":
        return CollaborationBroadcaster(self.bus)

    def create_subscriber(self, handler: Callable[[TestEvent], Awaitable[None]]) -> "CollaborationSubscriber":
        subscriber = CollaborationSubscriber(self.bus, self.worker, handler)
        return subscriber


class CollaborationBroadcaster:
    """Publish collaboration events through event-kit."""

    def __init__(self, bus: EventBus):
        self.bus = bus

    async def broadcast(self, event: TestEvent) -> None:
        await self.bus.publish(TEST_EVENT_CHANNEL, event.to_bus_event().data)


class CollaborationSubscriber:
    """Subscribe to collaboration events using workflow-kit workers."""

    def __init__(
        self,
        bus: EventBus,
        worker: Worker,
        handler: Callable[[TestEvent], Awaitable[None]],
    ):
        self.bus = bus
        self.worker = worker
        self._handler = handler
        self._register_subscription()

    def _register_subscription(self) -> None:
        @task()
        async def process(event_payload: Dict[str, Any]):
            event = TestEvent(
                event_type=event_payload["event_type"],
                test_name=event_payload["test_name"],
                endpoint=event_payload["endpoint"],
                user=event_payload["user"],
                data=event_payload.get("data", {}),
                timestamp=event_payload.get("timestamp", datetime.utcnow()),
            )
            await self._handler(event)

        self.worker.register(process)

        async def _dispatch(payload: Dict[str, Any]):
            await process(payload)

        self.bus.subscribe(TEST_EVENT_CHANNEL, _dispatch)

    async def start(self) -> None:
        await self.worker.start()


__all__ = [
    "CollaborationFactory",
    "CollaborationBroadcaster",
    "CollaborationSubscriber",
    "TestEvent",
]
