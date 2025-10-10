"""File watching with event handling."""
from pathlib import Path
from typing import Callable, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio

class EventType(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"

@dataclass
class FileEvent:
    """File system event."""
    type: EventType
    path: str
    is_directory: bool = False

class FileWatcher:
    """Watch files for changes."""
    
    def __init__(self, path: str, patterns: List[str] = None, recursive: bool = True):
        """Initialize file watcher.
        
        Args:
            path: Path to watch
            patterns: File patterns to match (e.g., ["*.py", "*.txt"])
            recursive: Watch subdirectories
        """
        self.path = Path(path)
        self.patterns = patterns or ["*"]
        self.recursive = recursive
        self.handlers: List[Callable] = []
        self._running = False
    
    def on(self, event_type: EventType, handler: Callable):
        """Register event handler."""
        self.handlers.append((event_type, handler))
        return self
    
    def on_any(self, handler: Callable):
        """Register handler for any event."""
        self.handlers.append((None, handler))
        return self
    
    async def start(self):
        """Start watching (simplified mock implementation)."""
        self._running = True
        print(f"Watching {self.path} (patterns: {self.patterns})")
        
        # In production, use watchdog or similar library
        # This is a simplified mock
        while self._running:
            await asyncio.sleep(1)
    
    def stop(self):
        """Stop watching."""
        self._running = False
    
    async def _handle_event(self, event: FileEvent):
        """Handle file event."""
        for event_type, handler in self.handlers:
            if event_type is None or event_type == event.type:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
