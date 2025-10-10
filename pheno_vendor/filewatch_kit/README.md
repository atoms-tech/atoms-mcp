# Filewatch-Kit 👁️

File watching with event handling and filtering.

## Quick Start

```python
from filewatch_kit import FileWatcher, EventType

watcher = FileWatcher(
    path="./src",
    patterns=["*.py", "*.txt"],
    recursive=True
)

@watcher.on(EventType.MODIFIED)
async def on_modified(event):
    print(f"Modified: {event.path}")

@watcher.on_any
async def on_any_event(event):
    print(f"Event: {event.type.value} - {event.path}")

await watcher.start()
```

## Features

- Pattern-based filtering
- Recursive watching
- Event type filtering
- Async handlers

Note: Use with `watchdog` library in production for actual file watching.
