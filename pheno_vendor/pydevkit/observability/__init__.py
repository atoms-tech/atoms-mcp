"""Observability and monitoring utilities with KInfra integration."""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Optional KInfra integration
try:
    import kinfra
    HAS_KINFRA = True
except ImportError:
    HAS_KINFRA = False
    kinfra = None

class HealthMonitor:
    """Health monitoring with optional KInfra integration."""
    
    def __init__(self, service_name: str = "pydevkit"):
        self.service_name = service_name
        self._kinfra_instance = None
        
        if HAS_KINFRA:
            try:
                self._kinfra_instance = kinfra.KInfra()
                logger.info(f"KInfra integration enabled for {service_name}")
            except Exception as e:
                logger.warning(f"KInfra initialization failed: {e}")
                self._kinfra_instance = None
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric with optional KInfra integration."""
        if self._kinfra_instance:
            try:
                self._kinfra_instance.record_metric(
                    service=self.service_name,
                    metric=name,
                    value=value,
                    tags=tags or {}
                )
            except Exception as e:
                logger.warning(f"KInfra metric recording failed: {e}")
        else:
            # Fallback to standard logging
            logger.info(f"Metric {name}={value} tags={tags}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check with KInfra status."""
        status = {
            "service": self.service_name,
            "status": "healthy",
            "kinfra_available": HAS_KINFRA,
            "kinfra_enabled": self._kinfra_instance is not None
        }
        
        if self._kinfra_instance:
            try:
                kinfra_status = self._kinfra_instance.health_check()
                status["kinfra_status"] = kinfra_status
            except Exception as e:
                status["kinfra_error"] = str(e)
                status["kinfra_enabled"] = False
        
        return status

# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None

def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor("pydevkit")
    return _health_monitor

__all__ = ["HealthMonitor", "get_health_monitor", "HAS_KINFRA"]