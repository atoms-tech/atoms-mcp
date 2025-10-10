"""Persistent event store for event sourcing and audit logging."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass, asdict, field
from uuid import uuid4


@dataclass
class StoredEvent:
    """Event stored in the event store."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""
    aggregate_id: str = ""
    aggregate_type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoredEvent":
        """Create from dictionary."""
        return cls(**data)


class EventStoreBackend(Protocol):
    """Protocol for event store backends."""
    
    async def append(self, event: StoredEvent) -> None:
        """Append event to store."""
        ...
    
    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        event_type: Optional[str] = None,
        from_version: Optional[int] = None,
    ) -> List[StoredEvent]:
        """Get events from store."""
        ...
    
    async def get_stream(self, aggregate_id: str) -> List[StoredEvent]:
        """Get all events for an aggregate."""
        ...


class InMemoryEventStore:
    """In-memory event store for testing and development."""
    
    def __init__(self):
        self._events: List[StoredEvent] = []
    
    async def append(self, event: StoredEvent) -> None:
        """Append event to store."""
        self._events.append(event)
    
    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        event_type: Optional[str] = None,
        from_version: Optional[int] = None,
    ) -> List[StoredEvent]:
        """Get events from store with filtering."""
        events = self._events
        
        if aggregate_id:
            events = [e for e in events if e.aggregate_id == aggregate_id]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if from_version is not None:
            events = [e for e in events if e.version >= from_version]
        
        return events
    
    async def get_stream(self, aggregate_id: str) -> List[StoredEvent]:
        """Get all events for an aggregate in order."""
        return [e for e in self._events if e.aggregate_id == aggregate_id]


class FileEventStore:
    """File-based event store for persistence."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_stream_file(self, aggregate_id: str) -> Path:
        """Get file path for aggregate stream."""
        return self.storage_path / f"{aggregate_id}.jsonl"
    
    async def append(self, event: StoredEvent) -> None:
        """Append event to file."""
        stream_file = self._get_stream_file(event.aggregate_id)
        
        with stream_file.open("a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")
    
    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        event_type: Optional[str] = None,
        from_version: Optional[int] = None,
    ) -> List[StoredEvent]:
        """Get events from files with filtering."""
        events = []
        
        # If aggregate_id specified, only read that file
        if aggregate_id:
            stream_file = self._get_stream_file(aggregate_id)
            if stream_file.exists():
                events.extend(await self._read_stream_file(stream_file))
        else:
            # Read all stream files
            for stream_file in self.storage_path.glob("*.jsonl"):
                events.extend(await self._read_stream_file(stream_file))
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if from_version is not None:
            events = [e for e in events if e.version >= from_version]
        
        return sorted(events, key=lambda e: e.timestamp)
    
    async def get_stream(self, aggregate_id: str) -> List[StoredEvent]:
        """Get all events for an aggregate."""
        stream_file = self._get_stream_file(aggregate_id)
        
        if not stream_file.exists():
            return []
        
        return await self._read_stream_file(stream_file)
    
    async def _read_stream_file(self, file_path: Path) -> List[StoredEvent]:
        """Read events from a stream file."""
        events = []
        
        with file_path.open("r") as f:
            for line in f:
                if line.strip():
                    event_data = json.loads(line)
                    events.append(StoredEvent.from_dict(event_data))
        
        return events


class EventStore:
    """
    Event store for event sourcing and audit logging.
    
    Features:
    - Append-only event log
    - Aggregate streams
    - Event replay
    - Multiple backends (in-memory, file-based)
    
    Example:
        # In-memory store
        store = EventStore()
        
        # Append event
        event = StoredEvent(
            event_type="OrderPlaced",
            aggregate_id="order-123",
            aggregate_type="Order",
            data={"amount": 100, "items": 3},
            metadata={"user_id": "user-456"}
        )
        await store.append(event)
        
        # Get events for aggregate
        events = await store.get_stream("order-123")
        
        # Get all events of a type
        orders = await store.get_events(event_type="OrderPlaced")
        
        # File-based store
        file_store = EventStore(backend=FileEventStore(Path(".events")))
        await file_store.append(event)
    """
    
    def __init__(self, backend: Optional[EventStoreBackend] = None):
        self.backend = backend or InMemoryEventStore()
    
    async def append(
        self,
        event_type: str,
        aggregate_id: str,
        aggregate_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        version: int = 1,
    ) -> StoredEvent:
        """
        Append event to store.
        
        Args:
            event_type: Type of event (e.g., "OrderPlaced")
            aggregate_id: ID of the aggregate
            aggregate_type: Type of aggregate (e.g., "Order")
            data: Event data
            metadata: Optional metadata
            version: Event version number
            
        Returns:
            The stored event with generated ID and timestamp
        """
        event = StoredEvent(
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            data=data,
            metadata=metadata or {},
            version=version,
        )
        
        await self.backend.append(event)
        return event
    
    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        event_type: Optional[str] = None,
        from_version: Optional[int] = None,
    ) -> List[StoredEvent]:
        """
        Get events from store with filtering.
        
        Args:
            aggregate_id: Filter by aggregate ID
            event_type: Filter by event type
            from_version: Get events from version onwards
            
        Returns:
            List of matching events
        """
        return await self.backend.get_events(aggregate_id, event_type, from_version)
    
    async def get_stream(self, aggregate_id: str) -> List[StoredEvent]:
        """
        Get all events for an aggregate in order.
        
        Args:
            aggregate_id: The aggregate ID
            
        Returns:
            List of events for the aggregate
        """
        return await self.backend.get_stream(aggregate_id)
    
    async def replay(self, aggregate_id: str, reducer: Any) -> Any:
        """
        Replay events to rebuild aggregate state.
        
        Args:
            aggregate_id: The aggregate ID
            reducer: Function (state, event) -> new_state
            
        Returns:
            The final state after replaying all events
        """
        events = await self.get_stream(aggregate_id)
        state = None
        
        for event in events:
            state = reducer(state, event)
        
        return state
