"""
Core types and data structures for the cloud provider abstraction layer.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class ResourceType(str, Enum):
    """Cloud resource types."""
    # Compute
    COMPUTE_VM = "compute.vm"
    COMPUTE_CONTAINER = "compute.container"
    COMPUTE_FUNCTION = "compute.function"
    COMPUTE_EDGE = "compute.edge"

    # Database
    DATABASE_SQL = "database.sql"
    DATABASE_NOSQL = "database.nosql"
    DATABASE_SERVERLESS = "database.serverless"

    # Storage
    STORAGE_OBJECT = "storage.object"
    STORAGE_BLOCK = "storage.block"
    STORAGE_FILE = "storage.file"

    # Network
    NETWORK_LOAD_BALANCER = "network.loadbalancer"
    NETWORK_CDN = "network.cdn"
    NETWORK_DNS = "network.dns"
    NETWORK_VPC = "network.vpc"


class DeploymentState(str, Enum):
    """Deployment states."""
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    BUILDING = "BUILDING"
    PROVISIONING = "PROVISIONING"
    DEPLOYING = "DEPLOYING"
    HEALTH_CHECK = "HEALTH_CHECK"
    ACTIVE = "ACTIVE"
    UPDATING = "UPDATING"
    SCALING = "SCALING"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    ROLLING_BACK = "ROLLING_BACK"
    DELETING = "DELETING"
    DELETED = "DELETED"


class DeploymentStrategy(str, Enum):
    """Deployment strategies."""
    ROLLING = "rolling"
    BLUE_GREEN = "bluegreen"
    CANARY = "canary"
    ATOMIC = "atomic"
    RECREATE = "recreate"


class Capability(str, Enum):
    """Provider capabilities."""
    SCALABLE = "scalable"
    LOGGABLE = "loggable"
    EXECUTABLE = "executable"
    BACKUPABLE = "backupable"
    MONITORING = "monitoring"
    AUTO_SCALE = "autoscale"
    CUSTOM_DNS = "custom_dns"
    SSH = "ssh"


class HealthStatus(str, Enum):
    """Health check status."""
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    CHECKING = "CHECKING"


@dataclass
class HealthCheckConfig:
    """Health check configuration."""
    type: str  # http, tcp, command, custom
    interval: timedelta
    timeout: timedelta
    retries: int
    initial_delay: timedelta
    success_threshold: int
    failure_threshold: int
    path: Optional[str] = None
    port: Optional[int] = None
    command: Optional[str] = None


@dataclass
class RollbackConfig:
    """Rollback configuration."""
    enabled: bool
    max_retries: int
    retry_interval: timedelta


@dataclass
class DeployConfig:
    """Deployment configuration."""
    strategy: DeploymentStrategy
    health_check: Optional[HealthCheckConfig] = None
    timeout: Optional[timedelta] = None
    rollback: Optional[RollbackConfig] = None


@dataclass
class ResourceConfig:
    """Configuration for creating/updating a resource."""
    name: str
    type: ResourceType
    provider: str
    region: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    spec: Dict[str, Any] = field(default_factory=dict)
    deploy: Optional[DeployConfig] = None


@dataclass
class Endpoint:
    """Network endpoint."""
    type: str  # http, https, tcp, grpc
    url: str
    primary: bool
    port: Optional[int] = None
    protocol: Optional[str] = None


@dataclass
class Resource:
    """A deployed cloud resource."""
    id: str
    name: str
    type: ResourceType
    provider: str
    status: DeploymentState
    health_status: HealthStatus
    created_at: datetime
    updated_at: datetime
    region: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    endpoints: List[Endpoint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_deployed_at: Optional[datetime] = None


@dataclass
class DeploymentSource:
    """Deployment source configuration."""
    type: str  # git, docker, archive, inline
    repository: Optional[str] = None
    branch: Optional[str] = None
    commit: Optional[str] = None
    image: Optional[str] = None
    tag: Optional[str] = None
    path: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class DeploymentConfig:
    """Full deployment configuration."""
    resource_id: str
    source: DeploymentSource
    strategy: DeploymentStrategy
    version: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentError:
    """Deployment error details."""
    code: str
    message: str
    details: Optional[Any] = None


@dataclass
class Deployment:
    """A deployment instance."""
    id: str
    resource_id: str
    version: str
    state: DeploymentState
    strategy: DeploymentStrategy
    progress: int  # 0-100
    started_at: datetime
    updated_at: datetime
    message: Optional[str] = None
    finished_at: Optional[datetime] = None
    error: Optional[DeploymentError] = None


@dataclass
class InstanceInfo:
    """Running instance information."""
    id: str
    state: str
    health: HealthStatus
    started_at: datetime
    region: Optional[str] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None


@dataclass
class DeploymentStatus:
    """Detailed deployment status."""
    deployment: Deployment
    health: HealthStatus
    instances: List[InstanceInfo] = field(default_factory=list)
    last_health_check: Optional[datetime] = None


@dataclass
class ResourceFilter:
    """Filter criteria for resources."""
    types: Optional[List[ResourceType]] = None
    providers: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    tags: Optional[Dict[str, str]] = None
    states: Optional[List[DeploymentState]] = None


@dataclass
class LogOptions:
    """Log retrieval options."""
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    tail: Optional[int] = None
    follow: bool = False
    filter: Optional[str] = None
    instance_id: Optional[str] = None


@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: datetime
    message: str
    level: Optional[str] = None
    instance_id: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


class LogStream(Protocol):
    """Protocol for log streams."""

    def __next__(self) -> LogEntry:
        """Get next log entry."""
        ...

    def __iter__(self):
        """Return iterator."""
        ...

    def close(self) -> None:
        """Close the stream."""
        ...


@dataclass
class MetricOptions:
    """Metric retrieval options."""
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    granularity: Optional[str] = None  # 1m, 5m, 1h, 1d
    instance_id: Optional[str] = None
    metric_names: Optional[List[str]] = None


@dataclass
class Metric:
    """A time-series metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class CostEstimate:
    """Cost estimation."""
    hourly_usd: float
    daily_usd: float
    monthly_usd: float
    breakdown: Dict[str, float]
    confidence: str  # high, medium, low
    currency: str
    last_updated: datetime


@dataclass
class Cost:
    """Actual incurred cost."""
    total_usd: float
    breakdown: Dict[str, float]
    start_time: datetime
    end_time: datetime
    currency: str


@dataclass
class TimeRange:
    """Time range for queries."""
    start: datetime
    end: datetime


@dataclass
class Credentials:
    """Authentication credentials."""
    type: str  # iam, token, api_key, oauth, service_account
    data: Dict[str, str]
    region: Optional[str] = None
    endpoint: Optional[str] = None


@dataclass
class Region:
    """Geographic region."""
    id: str
    name: str
    location: str
    available: bool
    deprecated: bool = False
    zones: List[str] = field(default_factory=list)


@dataclass
class ProviderMetadata:
    """Provider metadata and capabilities."""
    name: str
    version: str
    supported_resources: List[ResourceType]
    capabilities: List[Capability]
    regions: List[Region]
    auth_types: List[str]
    description: str


@dataclass
class ScalePolicy:
    """Scaling policy."""
    cooldown: timedelta
    step: int
    threshold: int


@dataclass
class ScaleConfig:
    """Scaling configuration."""
    min_instances: int
    max_instances: int
    target_cpu: Optional[int] = None
    target_memory: Optional[int] = None
    target_requests: Optional[int] = None
    scale_up_policy: Optional[ScalePolicy] = None
    scale_down_policy: Optional[ScalePolicy] = None


@dataclass
class BackupConfig:
    """Backup configuration."""
    enabled: bool
    retention_days: int
    point_in_time_recovery: bool
    schedule: Optional[str] = None
    backup_window: Optional[str] = None


@dataclass
class Backup:
    """A backup instance."""
    id: str
    resource_id: str
    type: str  # full, incremental, snapshot
    status: str
    size_bytes: int
    started_at: datetime
    completed_at: Optional[datetime] = None


@dataclass
class AlertConfig:
    """Alert configuration."""
    id: str
    resource_id: str
    metric_name: str
    condition: str  # >, <, >=, <=, ==
    threshold: float
    duration: int  # seconds
    severity: str  # info, warning, critical
    actions: List[Dict[str, Any]]
    enabled: bool
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class AlertAction:
    """Alert action."""
    type: str  # email, webhook, sns, pagerduty
    target: str
    config: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthCheckStatus:
    """Health check status."""
    status: HealthStatus
    last_check: datetime
    consecutive_passes: int
    consecutive_fails: int
    details: Optional[str] = None


@dataclass
class Migration:
    """Database migration."""
    id: str
    name: str
    status: str  # pending, applied, failed, rolled_back
    sql: Optional[str] = None
    script_path: Optional[str] = None
    checksum: Optional[str] = None
    applied_at: Optional[datetime] = None


@dataclass
class PoolConfig:
    """Connection pool configuration."""
    min_connections: int
    max_connections: int
    connection_timeout: int  # seconds
    idle_timeout: int  # seconds
    max_lifetime: int  # seconds


@dataclass
class ProjectConfig:
    """Multi-resource project configuration."""
    name: str
    version: str
    environment: str
    providers: Dict[str, Credentials]
    resources: List[ResourceConfig]
    region: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ResourceDependency:
    """Resource dependency definition."""
    resource: str
    depends_on: List[str]
    wait_for: Optional[str] = None


@dataclass
class ProjectDeployment:
    """A deployed project."""
    id: str
    name: str
    environment: str
    version: str
    status: DeploymentState
    resources: List[Resource]
    deployments: List[Deployment]
    started_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime] = None


@dataclass
class ProjectStatus:
    """Overall project status."""
    project: ProjectDeployment
    health: HealthStatus
    resources: Dict[str, DeploymentStatus]
    cost_estimate: Optional[CostEstimate] = None
    actual_cost: Optional[Cost] = None
