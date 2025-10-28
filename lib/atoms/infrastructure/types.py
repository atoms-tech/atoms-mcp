"""Deployment and infrastructure type definitions."""

from enum import Enum
from typing import Optional, Dict, Any


class DeploymentEnvironment(Enum):
    """Environment enumeration for deployments."""
    LOCAL = "local"
    PREVIEW = "preview"
    PRODUCTION = "production"


class DeploymentResult:
    """Deployment result wrapper."""
    def __init__(self, success: bool, message: str = ""):
        self.success = success
        self.message = message


class DeploymentProvider:
    """Base provider interface."""
    def deploy(self, config: 'DeploymentConfig') -> DeploymentResult:
        """Deploy with given configuration."""
        raise NotImplementedError


class HTTPHealthCheckProvider(DeploymentProvider):
    """HTTP-based health check provider."""
    def __init__(self, url: str, timeout: int = 30):
        self.url = url
        self.timeout = timeout
    
    def deploy(self, config: 'DeploymentConfig') -> DeploymentResult:
        """Deploy with HTTP health checks."""
        return DeploymentResult(True, f"HTTP health check deployed to {self.url}")


class VercelDeploymentProvider(DeploymentProvider):
    """Vercel-specific deployment provider."""
    def __init__(self, project_id: str, token: str):
        self.project_id = project_id
        self.token = token
    
    def deploy(self, config: 'DeploymentConfig') -> DeploymentResult:
        """Deploy to Vercel."""
        return DeploymentResult(True, f"Deployed to Vercel project {self.project_id}")


class DeploymentConfig:
    """Base deployment configuration."""
    def __init__(self, environment: DeploymentEnvironment, **kwargs):
        self.environment = environment
        self.config = kwargs