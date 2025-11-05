"""
Pheno tunnel provider adapter.

This module provides access to Pheno's tunnel functionality for
development and testing purposes.
"""

from __future__ import annotations

from typing import Any, Optional

try:
    from pheno.tunnel import TunnelProvider

    PHENO_TUNNEL_AVAILABLE = True
except ImportError:
    PHENO_TUNNEL_AVAILABLE = False
    TunnelProvider = None


class PhenoTunnelAdapter:
    """
    Adapter for Pheno tunnel functionality.

    This adapter provides a simplified interface to Pheno's tunnel
    capabilities for exposing local servers to the internet.
    """

    def __init__(
        self,
        subdomain: Optional[str] = None,
        port: int = 8000,
    ) -> None:
        """
        Initialize tunnel adapter.

        Args:
            subdomain: Optional custom subdomain
            port: Local port to tunnel

        Raises:
            RuntimeError: If Pheno tunnel is not available
        """
        if not PHENO_TUNNEL_AVAILABLE or not TunnelProvider:
            raise RuntimeError("Pheno tunnel is not available")

        self.subdomain = subdomain
        self.port = port
        self._tunnel: Optional[Any] = None
        self._public_url: Optional[str] = None

    def start(self) -> str:
        """
        Start the tunnel.

        Returns:
            Public URL for the tunnel

        Raises:
            RuntimeError: If tunnel fails to start
        """
        if self._tunnel is not None:
            return self._public_url or ""

        try:
            # Create tunnel provider
            provider = TunnelProvider()

            # Start tunnel
            self._tunnel = provider.create_tunnel(
                port=self.port,
                subdomain=self.subdomain,
            )

            # Get public URL
            self._public_url = self._tunnel.public_url

            return self._public_url

        except Exception as e:
            raise RuntimeError(f"Failed to start tunnel: {e}") from e

    def stop(self) -> None:
        """
        Stop the tunnel.
        """
        if self._tunnel is not None:
            try:
                self._tunnel.close()
            except Exception:
                pass
            finally:
                self._tunnel = None
                self._public_url = None

    @property
    def is_running(self) -> bool:
        """
        Check if tunnel is running.

        Returns:
            True if tunnel is active
        """
        return self._tunnel is not None

    @property
    def public_url(self) -> Optional[str]:
        """
        Get public URL.

        Returns:
            Public URL or None if tunnel not started
        """
        return self._public_url

    def __enter__(self) -> PhenoTunnelAdapter:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.stop()


# Global tunnel instance
_tunnel: Optional[PhenoTunnelAdapter] = None


def get_pheno_tunnel(
    subdomain: Optional[str] = None,
    port: int = 8000,
) -> Optional[PhenoTunnelAdapter]:
    """
    Get or create Pheno tunnel instance.

    Args:
        subdomain: Optional custom subdomain
        port: Local port to tunnel

    Returns:
        PhenoTunnelAdapter instance or None if not available
    """
    if not PHENO_TUNNEL_AVAILABLE:
        return None

    global _tunnel

    if _tunnel is None:
        try:
            from atoms_mcp.infrastructure.config.settings import get_settings

            settings = get_settings()

            # Use settings if provided
            if settings.pheno.tunnel_subdomain:
                subdomain = settings.pheno.tunnel_subdomain

            _tunnel = PhenoTunnelAdapter(subdomain=subdomain, port=port)
        except Exception:
            return None

    return _tunnel


def reset_tunnel() -> None:
    """
    Reset global tunnel instance.

    This stops any running tunnel and clears the instance.
    """
    global _tunnel

    if _tunnel is not None:
        _tunnel.stop()
        _tunnel = None
