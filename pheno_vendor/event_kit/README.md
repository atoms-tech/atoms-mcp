# Event-Kit

Event bus and webhook management for Python applications.

## Features

- **Event Bus**: In-memory pub/sub with wildcard patterns
- **Event Store**: Event sourcing with replay capabilities  
- **Webhook Manager**: Reliable webhook delivery with retries
- **HMAC Signatures**: Secure webhook signing and verification

## Installation

```bash
pip install event-kit
```

## Quick Start

### Event Bus

```python
from event_kit import EventBus

bus = EventBus()

@bus.on("user.created")
async def send_welcome_email(event):
    await email.send(event.data["email"])

await bus.publish("user.created", {"email": "user@example.com"})
```

### Event Store

```python
from event_kit import EventStore

store = EventStore()

await store.append(
    event_type="OrderPlaced",
    aggregate_id="order-123",
    aggregate_type="Order",
    data={"amount": 100}
)

events = await store.get_stream("order-123")
```

### Webhooks

```python
from event_kit import WebhookManager

manager = WebhookManager(secret="my-secret-key")

webhook_id = await manager.deliver(
    url="https://example.com/webhook",
    event_type="order.placed",
    payload={"order_id": "123"}
)

await manager.process_pending()
```

## Documentation

See `/examples` for complete examples.
