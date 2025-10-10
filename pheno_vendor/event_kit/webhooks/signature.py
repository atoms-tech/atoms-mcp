"""HMAC signature generation and verification for webhooks."""

import hashlib
import hmac


class WebhookSigner:
    """
    HMAC signature generator for webhooks.
    
    Example:
        signer = WebhookSigner("my-secret-key")
        signature = signer.sign('{"event": "user.created"}')
    """
    
    def __init__(self, secret: str):
        self.secret = secret.encode()
    
    def sign(self, payload: str) -> str:
        """
        Generate HMAC-SHA256 signature.
        
        Args:
            payload: JSON string to sign
            
        Returns:
            Signature in format "sha256=..."
        """
        signature = hmac.new(
            self.secret,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    @staticmethod
    def verify(payload: str, signature: str, secret: str) -> bool:
        """
        Verify HMAC signature.
        
        Args:
            payload: JSON string
            signature: Signature to verify
            secret: Secret key
            
        Returns:
            True if signature is valid
        """
        signer = WebhookSigner(secret)
        expected = signer.sign(payload)
        return hmac.compare_digest(expected, signature)


class WebhookReceiver:
    """
    Webhook receiver with signature verification.
    
    Example:
        receiver = WebhookReceiver("my-secret-key")
        
        if receiver.verify(payload, signature):
            process_webhook(payload)
    """
    
    def __init__(self, secret: str):
        self.signer = WebhookSigner(secret)
    
    def verify(self, payload: str, signature: str) -> bool:
        """Verify webhook signature."""
        return WebhookSigner.verify(payload, signature, self.signer.secret.decode())
