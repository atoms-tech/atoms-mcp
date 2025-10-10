"""Webhook delivery manager with retries and monitoring."""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from .signature import WebhookSigner
from .retry import RetryPolicy


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


class WebhookManager:
    """
    Webhook delivery manager.
    
    Features:
    - Async HTTP delivery
    - HMAC signatures
    - Automatic retries
    - Delivery tracking
    
    Example:
        manager = WebhookManager(secret="my-secret")
        
        webhook_id = await manager.deliver(
            url="https://example.com/webhook",
            event_type="order.placed",
            payload={"order_id": "123"}
        )
        
        await manager.process_pending()
    """
    
    def __init__(
        self,
        secret: Optional[str] = None,
        retry_policy: Optional[RetryPolicy] = None,
        timeout: int = 30,
    ):
        if not HAS_HTTPX:
            raise ImportError("httpx required: pip install httpx")
        
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
    
    def on_success(self, callback: Callable):
        """Register success callback."""
        self._success_callbacks.append(callback)
        return callback
    
    def on_failure(self, callback: Callable):
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
            url: Webhook endpoint
            event_type: Event type
            payload: Event data
            max_attempts: Override max attempts
            
        Returns:
            Delivery ID
        """
        delivery = WebhookDelivery(
            url=url,
            payload=payload,
            event_type=event_type,
            max_attempts=max_attempts or self.retry_policy.max_attempts,
        )
        
        self._deliveries[delivery.id] = delivery
        await self._attempt_delivery(delivery)
        
        return delivery.id
    
    async def _attempt_delivery(self, delivery: WebhookDelivery) -> bool:
        """Attempt webhook delivery."""
        delivery.attempts += 1
        delivery.status = WebhookStatus.RETRYING
        
        try:
            payload_str = json.dumps(delivery.payload)
            
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Event": delivery.event_type,
                "X-Webhook-ID": delivery.id,
                "X-Webhook-Attempt": str(delivery.attempts),
            }
            
            if self.signer:
                headers["X-Webhook-Signature"] = self.signer.sign(payload_str)
            
            client = await self._get_client()
            response = await client.post(
                delivery.url,
                content=payload_str,
                headers=headers,
            )
            
            if 200 <= response.status_code < 300:
                delivery.status = WebhookStatus.DELIVERED
                delivery.delivered_at = datetime.utcnow()
                delivery.last_error = None
                
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
            
            if delivery.attempts < delivery.max_attempts:
                delivery.status = WebhookStatus.RETRYING
                delivery.next_retry = self.retry_policy.next_retry_time(delivery.attempts)
            else:
                delivery.status = WebhookStatus.FAILED
                
                for callback in self._failure_callbacks:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(delivery)
                    else:
                        callback(delivery)
            
            return False
    
    async def process_pending(self):
        """Process all pending deliveries."""
        pending = [d for d in self._deliveries.values() if d.should_retry()]
        tasks = [self._attempt_delivery(d) for d in pending]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery by ID."""
        return self._deliveries.get(delivery_id)
    
    def get_stats(self) -> Dict[str, int]:
        """Get delivery statistics."""
        return {
            "total": len(self._deliveries),
            "delivered": sum(1 for d in self._deliveries.values() if d.status == WebhookStatus.DELIVERED),
            "pending": sum(1 for d in self._deliveries.values() if d.status in (WebhookStatus.PENDING, WebhookStatus.RETRYING)),
            "failed": sum(1 for d in self._deliveries.values() if d.status == WebhookStatus.FAILED),
        }
