"""Webhook delivery system with retries, HMAC signing, and monitoring."""

import asyncio
import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class WebhookStatus(Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookDelivery:
    """Webhook delivery record."""

    id: str = field(default_factory=lambda: str(uuid4()))
    url: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    event_type: str = ""
    status: WebhookStatus = WebhookStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    next_retry: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None

    def should_retry(self) -> bool:
        """Check if should retry delivery."""
        return (
            self.status in (WebhookStatus.PENDING, WebhookStatus.RETRYING, WebhookStatus.FAILED)
            and self.attempts < self.max_attempts
            and (self.next_retry is None or datetime.utcnow() >= self.next_retry)
        )


class WebhookSigner:
    """HMAC signature generator for webhooks."""

    def __init__(self, secret: str):
        self.secret = secret.encode()

    def sign(self, payload: str) -> str:
        """Generate HMAC signature for payload."""
        signature = hmac.new(
            self.secret,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    @staticmethod
    def verify(payload: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature."""
        signer = WebhookSigner(secret)
        expected = signer.sign(payload)
        return hmac.compare_digest(expected, signature)


class RetryPolicy:
    """Retry policy for webhook delivery."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: int = 60,  # seconds
        multiplier: float = 2.0,
        max_delay: int = 3600,  # 1 hour
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.multiplier = multiplier
        self.max_delay = max_delay

    def next_retry_time(self, attempt: int) -> datetime:
        """Calculate next retry time using exponential backoff."""
        delay = min(
            self.initial_delay * (self.multiplier ** attempt),
            self.max_delay
        )
        return datetime.utcnow() + timedelta(seconds=delay)


class WebhookManager:
    """
    Webhook delivery manager with retries and HMAC signing.
    
    Features:
    - Async HTTP delivery
    - HMAC-SHA256 signatures
    - Exponential backoff retries
    - Delivery tracking
    - Event callbacks
    
    Example:
        manager = WebhookManager(secret="my-secret-key")
        
        # Register webhook
        webhook_id = await manager.deliver(
            url="https://example.com/webhook",
            event_type="order.placed",
            payload={"order_id": "123", "amount": 100}
        )
        
        # Check status
        delivery = manager.get_delivery(webhook_id)
        print(f"Status: {delivery.status}")
        
        # Register callback
        @manager.on_success
        async def handle_success(delivery):
            print(f"Delivered: {delivery.id}")
        
        # Process pending deliveries
        await manager.process_pending()
    """

    def __init__(
        self,
        secret: Optional[str] = None,
        retry_policy: Optional[RetryPolicy] = None,
        timeout: int = 30,
    ):
        if not HAS_HTTPX:
            raise ImportError("httpx is required for WebhookManager. Install with: pip install httpx")

        self.secret = secret
        self.signer = WebhookSigner(secret) if secret else None
        self.retry_policy = retry_policy or RetryPolicy()
        self.timeout = timeout

        self._deliveries: Dict[str, WebhookDelivery] = {}
        self._success_callbacks: List[Callable] = []
        self._failure_callbacks: List[Callable] = []
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def on_success(self, callback: Callable[[WebhookDelivery], Any]):
        """Register success callback."""
        self._success_callbacks.append(callback)
        return callback

    def on_failure(self, callback: Callable[[WebhookDelivery], Any]):
        """Register failure callback."""
        self._failure_callbacks.append(callback)
        return callback

    async def deliver(
        self,
        url: str,
        event_type: str,
        payload: Dict[str, Any],
        max_attempts: Optional[int] = None,
    ) -> str:
        """
        Queue webhook for delivery.
        
        Args:
            url: Webhook endpoint URL
            event_type: Type of event (e.g., "order.placed")
            payload: Event data
            max_attempts: Override max retry attempts
            
        Returns:
            Webhook delivery ID
        """
        delivery = WebhookDelivery(
            url=url,
            payload=payload,
            event_type=event_type,
            max_attempts=max_attempts or self.retry_policy.max_attempts,
        )

        self._deliveries[delivery.id] = delivery

        # Attempt immediate delivery
        await self._attempt_delivery(delivery)

        return delivery.id

    async def _attempt_delivery(self, delivery: WebhookDelivery) -> bool:
        """
        Attempt webhook delivery.
        
        Returns:
            True if successful, False otherwise
        """
        delivery.attempts += 1
        delivery.status = WebhookStatus.RETRYING

        try:
            # Prepare payload
            payload_str = json.dumps(delivery.payload)

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Event": delivery.event_type,
                "X-Webhook-ID": delivery.id,
                "X-Webhook-Attempt": str(delivery.attempts),
            }

            # Add signature if secret configured
            if self.signer:
                headers["X-Webhook-Signature"] = self.signer.sign(payload_str)

            # Send request
            client = await self._get_client()
            response = await client.post(
                delivery.url,
                content=payload_str,
                headers=headers,
            )

            # Check response
            if 200 <= response.status_code < 300:
                delivery.status = WebhookStatus.DELIVERED
                delivery.delivered_at = datetime.utcnow()
                delivery.last_error = None

                # Trigger success callbacks
                for callback in self._success_callbacks:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(delivery)
                    else:
                        callback(delivery)

                return True
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            delivery.last_error = str(e)

            # Schedule retry or mark as failed
            if delivery.attempts < delivery.max_attempts:
                delivery.status = WebhookStatus.RETRYING
                delivery.next_retry = self.retry_policy.next_retry_time(delivery.attempts)
            else:
                delivery.status = WebhookStatus.FAILED

                # Trigger failure callbacks
                for callback in self._failure_callbacks:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(delivery)
                    else:
                        callback(delivery)

            return False

    async def process_pending(self):
        """Process all pending webhook deliveries."""
        pending = [
            d for d in self._deliveries.values()
            if d.should_retry()
        ]

        tasks = [self._attempt_delivery(d) for d in pending]
        await asyncio.gather(*tasks, return_exceptions=True)

    def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery record by ID."""
        return self._deliveries.get(delivery_id)

    def get_pending(self) -> List[WebhookDelivery]:
        """Get all pending deliveries."""
        return [
            d for d in self._deliveries.values()
            if d.status in (WebhookStatus.PENDING, WebhookStatus.RETRYING)
        ]

    def get_failed(self) -> List[WebhookDelivery]:
        """Get all failed deliveries."""
        return [
            d for d in self._deliveries.values()
            if d.status == WebhookStatus.FAILED
        ]

    def get_stats(self) -> Dict[str, int]:
        """Get delivery statistics."""
        return {
            "total": len(self._deliveries),
            "delivered": sum(1 for d in self._deliveries.values() if d.status == WebhookStatus.DELIVERED),
            "pending": sum(1 for d in self._deliveries.values() if d.status in (WebhookStatus.PENDING, WebhookStatus.RETRYING)),
            "failed": sum(1 for d in self._deliveries.values() if d.status == WebhookStatus.FAILED),
        }


class WebhookReceiver:
    """
    Webhook receiver with signature verification.
    
    Example:
        receiver = WebhookReceiver(secret="my-secret-key")
        
        @app.post("/webhook")
        async def handle_webhook(request):
            # Verify signature
            payload = await request.body()
            signature = request.headers.get("X-Webhook-Signature")
            
            if not receiver.verify(payload, signature):
                return {"error": "Invalid signature"}, 401
            
            # Process webhook
            data = await request.json()
            await process_event(data)
            
            return {"status": "ok"}
    """

    def __init__(self, secret: str):
        self.signer = WebhookSigner(secret)

    def verify(self, payload: str, signature: str) -> bool:
        """Verify webhook signature."""
        return WebhookSigner.verify(payload, signature, self.signer.secret.decode())
