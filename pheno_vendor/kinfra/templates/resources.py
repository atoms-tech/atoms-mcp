"""
Resource Templates - Pre-configured templates for common system resources

Provides easy-to-use templates that can be customized as needed.
All templates return config dictionaries that can be passed to ResourceFactory.
"""

from pathlib import Path
from typing import Any, Dict, Optional


def postgres(
    port: int = 5432,
    password: str = "postgres",
    database: str = "postgres",
    user: str = "postgres",
    version: str = "16-alpine",
    data_dir: Optional[Path] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    PostgreSQL template.

    Args:
        port: Host port (default: 5432)
        password: Postgres password
        database: Default database name
        user: Postgres user
        version: Postgres version tag
        data_dir: Optional data directory for persistence
        **kwargs: Additional Docker configuration

    Returns:
        Resource configuration dict

    Example:
        >>> from kinfra.templates.resources import postgres
        >>> from kinfra.adapters import resource_from_dict
        >>> pg = resource_from_dict("db", postgres(port=5433, password="secret"))
        >>> await pg.start()
    """
    config = {
        "type": "docker",
        "image": f"postgres:{version}",
        "container_name": kwargs.get("container_name", f"kinfra-postgres-{port}"),
        "ports": {port: 5432},
        "environment": {
            "POSTGRES_PASSWORD": password,
            "POSTGRES_DB": database,
            "POSTGRES_USER": user
        },
        "health_check": {
            "type": "tcp",
            "port": port
        },
        "cleanup_on_stop": kwargs.get("cleanup_on_stop", True),
        "restart_policy": kwargs.get("restart_policy", "unless-stopped")
    }

    if data_dir:
        config["volumes"] = {str(data_dir): "/var/lib/postgresql/data"}

    # Merge any additional kwargs
    config.update({k: v for k, v in kwargs.items() if k not in config})

    return config


def nats(
    port: int = 4222,
    enable_jetstream: bool = True,
    version: str = "latest",
    data_dir: Optional[Path] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    NATS template.

    Args:
        port: Host port (default: 4222)
        enable_jetstream: Enable JetStream (default: True)
        version: NATS version tag
        data_dir: Optional data directory for JetStream persistence
        **kwargs: Additional Docker configuration

    Returns:
        Resource configuration dict
    """
    command = []
    if enable_jetstream:
        command = ["-js"]
        if data_dir:
            command.extend(["-sd", "/data"])

    config = {
        "type": "docker",
        "image": f"nats:{version}",
        "container_name": kwargs.get("container_name", f"kinfra-nats-{port}"),
        "ports": {port: 4222},
        "command": command if command else None,
        "health_check": {
            "type": "tcp",
            "port": port
        },
        "cleanup_on_stop": kwargs.get("cleanup_on_stop", True),
        "restart_policy": kwargs.get("restart_policy", "unless-stopped")
    }

    if data_dir and enable_jetstream:
        config["volumes"] = {str(data_dir): "/data"}

    config.update({k: v for k, v in kwargs.items() if k not in config})

    return config


def redis(
    port: int = 6379,
    enable_persistence: bool = True,
    version: str = "7-alpine",
    data_dir: Optional[Path] = None,
    **kwargs
) -> Dict[str, Any]:
    """Redis template."""
    command = []
    if enable_persistence:
        command = ["redis-server", "--appendonly", "yes"]

    config = {
        "type": "docker",
        "image": f"redis:{version}",
        "container_name": kwargs.get("container_name", f"kinfra-redis-{port}"),
        "ports": {port: 6379},
        "command": command if command else None,
        "health_check": {
            "type": "tcp",
            "port": port
        },
        "cleanup_on_stop": kwargs.get("cleanup_on_stop", True),
        "restart_policy": kwargs.get("restart_policy", "unless-stopped")
    }

    if data_dir and enable_persistence:
        config["volumes"] = {str(data_dir): "/data"}

    config.update({k: v for k, v in kwargs.items() if k not in config})

    return config


def mongodb(
    port: int = 27017,
    version: str = "7",
    data_dir: Optional[Path] = None,
    **kwargs
) -> Dict[str, Any]:
    """MongoDB template."""
    config = {
        "type": "docker",
        "image": f"mongo:{version}",
        "container_name": kwargs.get("container_name", f"kinfra-mongodb-{port}"),
        "ports": {port: 27017},
        "health_check": {
            "type": "tcp",
            "port": port
        },
        "cleanup_on_stop": kwargs.get("cleanup_on_stop", True),
        "restart_policy": kwargs.get("restart_policy", "unless-stopped")
    }

    if data_dir:
        config["volumes"] = {str(data_dir): "/data/db"}

    config.update({k: v for k, v in kwargs.items() if k not in config})

    return config


def mysql(
    port: int = 3306,
    password: str = "mysql",
    database: str = "mysql",
    version: str = "8",
    data_dir: Optional[Path] = None,
    **kwargs
) -> Dict[str, Any]:
    """MySQL template."""
    config = {
        "type": "docker",
        "image": f"mysql:{version}",
        "container_name": kwargs.get("container_name", f"kinfra-mysql-{port}"),
        "ports": {port: 3306},
        "environment": {
            "MYSQL_ROOT_PASSWORD": password,
            "MYSQL_DATABASE": database
        },
        "health_check": {
            "type": "tcp",
            "port": port
        },
        "cleanup_on_stop": kwargs.get("cleanup_on_stop", True),
        "restart_policy": kwargs.get("restart_policy", "unless-stopped")
    }

    if data_dir:
        config["volumes"] = {str(data_dir): "/var/lib/mysql"}

    config.update({k: v for k, v in kwargs.items() if k not in config})

    return config


def custom_docker(
    image: str,
    port: Optional[int] = None,
    ports: Optional[Dict[int, int]] = None,
    environment: Optional[Dict[str, str]] = None,
    volumes: Optional[Dict[str, str]] = None,
    command: Optional[list] = None,
    health_check_port: Optional[int] = None,
    health_check_type: str = "tcp",
    **kwargs
) -> Dict[str, Any]:
    """
    Generic Docker container template.

    Args:
        image: Docker image (required)
        port: Single port mapping (host=container)
        ports: Multiple port mappings {host: container}
        environment: Environment variables
        volumes: Volume mounts {host_path: container_path}
        command: Command override
        health_check_port: Port for health checks
        health_check_type: Health check type (tcp, http, docker)
        **kwargs: Additional Docker config

    Returns:
        Resource configuration dict

    Example:
        >>> elasticsearch = custom_docker(
        ...     image="elasticsearch:8.11.0",
        ...     ports={9200: 9200, 9300: 9300},
        ...     environment={"discovery.type": "single-node"},
        ...     health_check_port=9200,
        ...     health_check_type="http",
        ...     health_check_path="/_cluster/health"
        ... )
    """
    config = {
        "type": "docker",
        "image": image,
        "health_check": {},
        "cleanup_on_stop": kwargs.get("cleanup_on_stop", True),
        "restart_policy": kwargs.get("restart_policy", "unless-stopped")
    }

    # Handle ports
    if ports:
        config["ports"] = ports
    elif port:
        config["ports"] = {port: port}

    # Handle other options
    if environment:
        config["environment"] = environment
    if volumes:
        config["volumes"] = volumes
    if command:
        config["command"] = command

    # Health check
    if health_check_port:
        config["health_check"] = {
            "type": health_check_type,
            "port": health_check_port
        }
        if "health_check_path" in kwargs:
            config["health_check"]["path"] = kwargs.pop("health_check_path")

    # Merge remaining kwargs
    config.update({k: v for k, v in kwargs.items() if k not in config})

    return config


def systemd_service(
    service_name: str,
    health_check_port: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Systemd service template.

    Example:
        >>> nginx = systemd_service("nginx", health_check_port=80)
    """
    config = {
        "type": "systemd",
        "service_name": service_name,
        "use_sudo": kwargs.get("use_sudo", True)
    }

    if health_check_port:
        config["health_check"] = {
            "type": "tcp",
            "port": health_check_port
        }

    config.update({k: v for k, v in kwargs.items() if k not in config})

    return config


def custom_command(
    start_command: list,
    stop_command: list,
    status_command: Optional[list] = None,
    health_check_port: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Custom command-based resource template.

    Example:
        >>> my_service = custom_command(
        ...     start_command=["./start.sh"],
        ...     stop_command=["./stop.sh"],
        ...     health_check_port=8080
        ... )
    """
    config = {
        "type": "command",
        "start_command": start_command,
        "stop_command": stop_command,
        "run_in_background": kwargs.get("run_in_background", True)
    }

    if status_command:
        config["status_command"] = status_command

    if health_check_port:
        config["health_check"] = {
            "type": "tcp",
            "port": health_check_port
        }

    config.update({k: v for k, v in kwargs.items() if k not in config})

    return config


# =============================================================================
# API-Based / Cloud Resources
# =============================================================================

def api_resource(
    api_base_url: str,
    auth_type: str = "none",
    auth_token: Optional[str] = None,
    api_key: Optional[str] = None,
    start_endpoint: str = "/start",
    stop_endpoint: str = "/stop",
    health_endpoint: str = "/health",
    **kwargs
) -> Dict[str, Any]:
    """
    Generic API-based resource template.

    Args:
        api_base_url: Base URL for the API
        auth_type: Authentication type (none, bearer, api_key, basic)
        auth_token: Bearer token (if auth_type=bearer)
        api_key: API key (if auth_type=api_key)
        start_endpoint: Endpoint to start resource
        stop_endpoint: Endpoint to stop resource
        health_endpoint: Health check endpoint
        **kwargs: Additional configuration

    Example:
        >>> my_api = api_resource(
        ...     api_base_url="https://api.myservice.com",
        ...     auth_type="bearer",
        ...     auth_token="sk_123...",
        ...     start_endpoint="/v1/instances/start",
        ...     health_endpoint="/v1/instances/health"
        ... )
    """
    config = {
        "type": "api",
        "api_base_url": api_base_url,
        "start_endpoint": start_endpoint,
        "stop_endpoint": stop_endpoint,
        "status_endpoint": kwargs.get("status_endpoint", "/status"),
        "health_endpoint": health_endpoint
    }

    # Setup authentication
    auth_config = {"type": auth_type}
    if auth_type == "bearer" and auth_token:
        auth_config["token"] = auth_token
    elif auth_type == "api_key" and api_key:
        auth_config["api_key"] = api_key
        auth_config["header_name"] = kwargs.get("api_key_header", "X-API-Key")
    elif auth_type == "basic":
        auth_config["username"] = kwargs.get("username", "")
        auth_config["password"] = kwargs.get("password", "")

    config["auth"] = auth_config

    config.update({k: v for k, v in kwargs.items() if k not in config})

    return config


def supabase_project(
    project_id: str,
    access_token: Optional[str] = None,
    database_password: Optional[str] = None,
    use_sdk: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Supabase project template with native SDK support.

    Uses native Supabase Management API SDK when available, falls back to CLI.

    Args:
        project_id: Supabase project ID
        access_token: Access token (or set SUPABASE_ACCESS_TOKEN env var)
        database_password: Database password (for connection strings)
        use_sdk: Prefer SDK over CLI (default: True)
        **kwargs: Additional configuration

    Example:
        >>> supabase = supabase_project(
        ...     project_id="abcdefghij",
        ...     access_token="sbp_...",
        ...     database_password="your-db-password"
        ... )

    Returns:
        Config dict for SupabaseAdapter
    """
    config = {
        "type": "supabase",
        "project_id": project_id,
        "use_sdk": use_sdk
    }

    if access_token:
        config["access_token"] = access_token
    if database_password:
        config["database_password"] = database_password

    config.update(kwargs)
    return config


def render_service(
    service_id: str,
    api_key: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Render.com service template.

    Example:
        >>> render_api = render_service(
        ...     service_id="srv-123",
        ...     api_key="rnd_..."
        ... )
    """
    return api_resource(
        api_base_url=f"https://api.render.com/v1/services/{service_id}",
        auth_type="bearer",
        auth_token=api_key,
        start_endpoint="/resume",
        stop_endpoint="/suspend",
        health_endpoint="",
        status_endpoint="",
        **kwargs
    )


def aws_rds_instance(
    instance_id: str,
    region: str = "us-east-1",
    aws_access_key: Optional[str] = None,
    aws_secret_key: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    AWS RDS instance template (requires boto3).

    Example:
        >>> rds = aws_rds_instance(
        ...     instance_id="my-db-instance",
        ...     region="us-west-2"
        ... )
    """
    # Note: This would typically use boto3 SDK directly
    # Simplified API version for demonstration
    config = {
        "type": "api",
        "api_base_url": f"https://rds.{region}.amazonaws.com",
        "start_endpoint": f"/?Action=StartDBInstance&DBInstanceIdentifier={instance_id}",
        "stop_endpoint": f"/?Action=StopDBInstance&DBInstanceIdentifier={instance_id}",
        "status_endpoint": f"/?Action=DescribeDBInstances&DBInstanceIdentifier={instance_id}",
        "auth": {
            "type": "custom",
            "headers": {
                # Would need proper AWS signature v4
                "X-Amz-Access-Key": aws_access_key or "",
                "X-Amz-Secret-Key": aws_secret_key or ""
            }
        }
    }

    config.update(kwargs)
    return config


def vercel_deployment(
    project_name: Optional[str] = None,
    deployment_id: Optional[str] = None,
    team_id: Optional[str] = None,
    access_token: Optional[str] = None,
    target: str = "production",
    use_sdk: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Vercel deployment template with native SDK support.

    Uses Vercel SDK when available, falls back to CLI.

    Args:
        project_name: Vercel project name (for new deployments)
        deployment_id: Existing deployment ID (for promoting)
        team_id: Team ID (optional)
        access_token: Vercel token (or set VERCEL_TOKEN env var)
        target: Deployment target (production, preview, development)
        use_sdk: Prefer SDK over CLI (default: True)
        **kwargs: Additional configuration

    Example:
        >>> vercel = vercel_deployment(
        ...     project_name="my-app",
        ...     team_id="team_456",
        ...     access_token="tok_...",
        ...     target="production"
        ... )
    """
    config = {
        "type": "vercel",
        "target": target,
        "use_sdk": use_sdk
    }

    if project_name:
        config["project_name"] = project_name
    if deployment_id:
        config["deployment_id"] = deployment_id
    if team_id:
        config["team_id"] = team_id
    if access_token:
        config["access_token"] = access_token

    config.update(kwargs)
    return config


def neon_database(
    project_id: str,
    api_key: Optional[str] = None,
    branch_name: str = "main",
    region: Optional[str] = None,
    use_sdk: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Neon serverless Postgres template with native SDK support.

    Uses Neon API SDK when available, falls back to CLI.

    Args:
        project_id: Neon project ID
        api_key: Neon API key (or set NEON_API_KEY env var)
        branch_name: Branch name (default: main)
        region: AWS region (optional)
        use_sdk: Prefer SDK over CLI (default: True)
        **kwargs: Additional configuration

    Example:
        >>> neon = neon_database(
        ...     project_id="my-neon-project",
        ...     api_key="neon_...",
        ...     branch_name="main"
        ... )
    """
    config = {
        "type": "neon",
        "project_id": project_id,
        "branch_name": branch_name,
        "use_sdk": use_sdk
    }

    if api_key:
        config["api_key"] = api_key
    if region:
        config["region"] = region

    config.update(kwargs)
    return config


def railway_service(
    service_id: str,
    api_key: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Railway service template.

    Example:
        >>> railway = railway_service(
        ...     service_id="srv_123",
        ...     api_key="railway_..."
        ... )
    """
    return api_resource(
        api_base_url="https://backboard.railway.app/graphql/v2",
        auth_type="bearer",
        auth_token=api_key,
        start_endpoint="/",
        start_method="POST",
        start_body={
            "query": "mutation { serviceInstanceRedeploy(serviceId: $serviceId) { id } }",
            "variables": {"serviceId": service_id}
        },
        **kwargs
    )


def kubernetes_deployment(
    deployment_name: str,
    namespace: str = "default",
    kubeconfig: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Kubernetes deployment template (via kubectl).

    Example:
        >>> k8s_app = kubernetes_deployment(
        ...     deployment_name="my-app",
        ...     namespace="production"
        ... )
    """
    config = {
        "type": "command",
        "start_command": [
            "kubectl", "scale", "deployment", deployment_name,
            "--namespace", namespace, "--replicas=1"
        ],
        "stop_command": [
            "kubectl", "scale", "deployment", deployment_name,
            "--namespace", namespace, "--replicas=0"
        ],
        "status_command": [
            "kubectl", "get", "deployment", deployment_name,
            "--namespace", namespace, "-o", "jsonpath={.status.readyReplicas}"
        ]
    }

    if kubeconfig:
        for cmd in ["start_command", "stop_command", "status_command"]:
            config[cmd].extend(["--kubeconfig", kubeconfig])

    config.update(kwargs)
    return config


def custom_api(
    base_url: str,
    auth_token: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generic custom API resource.

    Maximally flexible - configure everything.

    Example:
        >>> custom = custom_api(
        ...     base_url="https://api.example.com",
        ...     auth_token="Bearer xxx",
        ...     start_endpoint="/v1/start",
        ...     start_method="POST",
        ...     start_body={"action": "deploy"},
        ...     health_endpoint="/v1/health"
        ... )
    """
    config = {
        "type": "api",
        "api_base_url": base_url
    }

    if auth_token:
        config["auth"] = {
            "type": "bearer",
            "token": auth_token
        }

    config.update(kwargs)
    return config

