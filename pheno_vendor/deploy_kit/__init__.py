"""Deploy-Kit - Universal deployment abstraction"""

from deploy_kit.local.manager import LocalProcessConfig, LocalServiceManager, ReadyProbe
from deploy_kit.nvms.parser import NVMSParser
from deploy_kit.platforms.modern.vercel import VercelClient
from deploy_kit.platforms.modern.fly import FlyClient
from deploy_kit.vendor import PhenoVendor, PackageInfo
from deploy_kit.config import DeployConfig, PackageDetector
from deploy_kit.utils import (
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
