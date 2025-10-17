"""Deploy-Kit - Universal deployment abstraction"""

from .local.manager import LocalProcessConfig, LocalServiceManager, ReadyProbe
from .nvms.parser import NVMSParser
from .platforms.modern.vercel import VercelClient
from .platforms.modern.fly import FlyClient
from .vendor import PhenoVendor, PackageInfo
from .config import DeployConfig, PackageDetector
from .utils import (
    PlatformDetector,
    PlatformInfo,
    BuildHookGenerator,
    DeploymentValidator,
    EnvironmentManager,
)

__version__ = "0.1.0"

__all__ = [
    # Local deployment
    "LocalProcessConfig",
    "LocalServiceManager",
    "ReadyProbe",
    # NVMS
    "NVMSParser",
    # Platform clients
    "VercelClient",
    "FlyClient",
    # Vendoring
    "PhenoVendor",
    "PackageInfo",
    # Configuration
    "DeployConfig",
    "PackageDetector",
    # Utilities
    "PlatformDetector",
    "PlatformInfo",
    "BuildHookGenerator",
    "DeploymentValidator",
    "EnvironmentManager",
]
