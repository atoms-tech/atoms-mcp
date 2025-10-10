"""
KInfra exception hierarchy for comprehensive error handling.
"""

class KInfraError(Exception):
    """Base exception for all KInfra operations."""
    pass

class PortAllocationError(KInfraError):
    """Raised when port allocation fails."""
    pass

class TunnelError(KInfraError):
    """Raised when tunnel operations fail."""
    pass

class ServiceConflictError(KInfraError):
    """Raised when service conflicts cannot be resolved."""
    pass

class ProcessManagementError(KInfraError):
    """Raised when process management operations fail."""
    pass

class ConfigurationError(KInfraError):
    """Raised when configuration is invalid or missing."""
    pass

class ServiceError(KInfraError):
    """Raised when service management operations fail."""
    pass
