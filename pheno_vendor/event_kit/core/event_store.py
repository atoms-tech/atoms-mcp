"""Event store for event sourcing and audit logging."""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class StoredEvent:
    """Event stored in event store."""
    
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


class EventStore:
    """
    Event store for event sourcing.
    
    Features:
    - Append-only event log
    - Aggregate streams
    - Event replay
    - Multiple backends
    
    Example:
        store = EventStore()
        
        # Append event
        await store.append(
            event_type="OrderPlaced",
            aggregate_id="order-123",
            aggregate_type="Order",
            data={"amount": 100}
        )
        
        # Get events for aggregate
        events = await store.get_stream("order-123")
        
        # Replay events
        state = await store.replay("order-123", reducer_fn)
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self._events: List[StoredEvent] = []
        
        if self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()
    
    def _load_from_disk(self):
        """Load events from disk."""
        if not self.storage_path:
            return
        
        for file in self.storage_path.glob("*.jsonl"):
            with file.open("r") as f:
                for line in f:
                    if line.strip():
                        event_data = json.loads(line)
                        self._events.append(StoredEvent.from_dict(event_data))
    
    def _get_stream_file(self, aggregate_id: str) -> Path:
        """Get file path for aggregate stream."""
        return self.storage_path / f"{aggregate_id}.jsonl"
    
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
            event_type: Type of event
            aggregate_id: Aggregate ID
            aggregate_type: Aggregate type
            data: Event data
            metadata: Optional metadata
            version: Event version
            
        Returns:
            Stored event
        """
        event = StoredEvent(
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            data=data,
            metadata=metadata or {},
            version=version,
        )
        
        self._events.append(event)
        
        # Persist to disk if configured
        if self.storage_path:
            stream_file = self._get_stream_file(aggregate_id)
            with stream_file.open("a") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        
        return event
    
    async def get_stream(self, aggregate_id: str) -> List[StoredEvent]:
        """Get all events for an aggregate."""
        return [e for e in self._events if e.aggregate_id == aggregate_id]
    
    async def get_events(
        self,
        event_type: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        from_version: Optional[int] = None,
    ) -> List[StoredEvent]:
        """Get events with filtering."""
        events = self._events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if aggregate_type:
            events = [e for e in events if e.aggregate_type == aggregate_type]
        
        if from_version is not None:
            events = [e for e in events if e.version >= from_version]
        
        return events
    
    async def replay(self, aggregate_id: str, reducer: Any) -> Any:
        """
        Replay events to rebuild state.
        
        Args:
            aggregate_id: Aggregate ID
            reducer: Function (state, event) -> new_state
            
        Returns:
            Final state
        """
        events = await self.get_stream(aggregate_id)
        state = None
        
        for event in events:
            state = reducer(state, event)
        
        return state
