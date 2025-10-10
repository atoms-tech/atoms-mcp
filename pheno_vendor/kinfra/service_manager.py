"""
Service Manager - Complete service lifecycle management for KInfra.

Extends KInfra with:
- Process startup and management
- Continuous health monitoring
- File watching and auto-reload
- Resource dependency checking
"""

import asyncio
import logging
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None

    # Create dummy classes when watchdog is not available
    class FileSystemEventHandler:
        pass

    class FileSystemEvent:
        pass

from .exceptions import KInfraError, ServiceError
from .kinfra import KInfra
from .utils.process import kill_processes_on_port
from .utils.health import check_http_health

logger = logging.getLogger(__name__)


class ServiceError(KInfraError):
    """Raised when service management operations fail."""
    pass


@dataclass
class ServiceConfig:
    """Configuration for a managed service."""
    name: str
    command: List[str]
    cwd: Optional[Path] = None
    env: Optional[Dict[str, str]] = None
    port: Optional[int] = None
    preferred_port: Optional[int] = None
    enable_tunnel: bool = False
    tunnel_domain: Optional[str] = None
    watch_paths: Optional[List[Path]] = None
    watch_patterns: Optional[List[str]] = None
    restart_on_failure: bool = True
    max_restart_attempts: int = 3
    restart_delay: float = 2.0
    health_check_url: Optional[str] = None
    health_check_interval: float = 10.0
    # Fallback server configuration
    enable_fallback: bool = True
    fallback_page: str = "loading"  # "loading", "503", "maintenance"
    fallback_refresh_interval: int = 5  # Auto-refresh interval in seconds
    fallback_message: Optional[str] = None  # Custom message for error page
    path_prefix: str = "/"  # Path prefix for routing (e.g., "/api")


@dataclass
class ResourceConfig:
    """Configuration for a resource dependency."""
    name: str
    host: str = "localhost"
    port: int = 5432
    check_interval: float = 10.0
    required: bool = True


@dataclass
class ServiceStatus:
    """Current status of a managed service."""
    name: str
    state: str  # "stopped", "starting", "running", "error", "reloading"
    pid: Optional[int] = None
    port: Optional[int] = None
    tunnel_url: Optional[str] = None
    started_at: Optional[datetime] = None
    restart_count: int = 0
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"  # "healthy", "unhealthy", "unknown"
    error_message: Optional[str] = None


@dataclass
class ResourceStatus:
    """Current status of a resource dependency."""
    name: str
    available: bool
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None


class FileChangeHandler(FileSystemEventHandler):
    """Handles file system events for auto-reload."""
    
    def __init__(self, callback: Callable[[FileSystemEvent], None], patterns: List[str]):
        super().__init__()
        self.callback = callback
        self.patterns = patterns or ['*.py']
        self._debounce_timer: Optional[asyncio.TimerHandle] = None
        self._debounce_delay = 1.0  # Wait 1 second before triggering reload
        
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        # Check if file matches patterns
        file_path = Path(event.src_path)
        if not any(file_path.match(pattern) for pattern in self.patterns):
            return
            
        logger.debug(f"File changed: {file_path}")
        self.callback(event)


class ServiceManager:
    """
    Complete service lifecycle manager with health monitoring and auto-reload.
    
    Features:
    - Process startup with port allocation
    - Cloudflare tunnel management
    - Continuous health monitoring
    - Resource dependency checking
    - File watching with auto-reload
    - Automatic restart on failure
    
    Usage:
        service_mgr = ServiceManager(kinfra)
        
        # Add service configuration
        service_mgr.add_service(ServiceConfig(
            name="zen-mcp-server",
            command=["python", "server.py"],
            preferred_port=8001,
            enable_tunnel=True,
            watch_paths=[Path(".")],
            watch_patterns=["*.py"]
        ))
        
        # Add resource dependencies
        service_mgr.add_resource(ResourceConfig(
            name="postgres",
            port=5432,
            required=True
        ))
        
        # Start all services
        await service_mgr.start_all()
        
        # Monitor continuously
        await service_mgr.monitor()
    """
    
    def __init__(self, kinfra: KInfra, enable_fallback_layer: bool = True, enable_resource_management: bool = True):
        """
        Initialize service manager.

        Args:
            kinfra: KInfra instance for port/tunnel management
            enable_fallback_layer: Enable automatic fallback server and proxy (default: True)
            enable_resource_management: Enable automatic Docker/system resource management (default: True)
        """
        self.kinfra = kinfra
        self.services: Dict[str, ServiceConfig] = {}
        self.resources: Dict[str, ResourceConfig] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.resource_status: Dict[str, ResourceStatus] = {}
        self.processes: Dict[str, asyncio.subprocess.Process] = {}
        self.file_observers: Dict[str, Observer] = {}
        self._shutdown = False
        self._monitor_tasks: List[asyncio.Task] = []

        # Fallback and proxy servers
        self.enable_fallback_layer = enable_fallback_layer
        self.fallback_server = None
        self.proxy_server = None
        self._fallback_started = False
        self._proxy_started = False

        # System resource manager (Docker, daemons, etc.)
        self.enable_resource_management = enable_resource_management
        self.resource_manager = None
        if enable_resource_management:
            from .resource_manager import ResourceManager
            self.resource_manager = ResourceManager()

        logger.info("ServiceManager initialized")
    
    def add_service(self, config: ServiceConfig):
        """
        Add a service configuration.
        
        Args:
            config: Service configuration
        """
        self.services[config.name] = config
        self.service_status[config.name] = ServiceStatus(
            name=config.name,
            state="stopped"
        )
        logger.info(f"Added service: {config.name}")
    
    def add_resource(self, config: ResourceConfig):
        """
        Add a resource dependency configuration (for health checks only).

        Args:
            config: Resource configuration
        """
        self.resources[config.name] = config
        self.resource_status[config.name] = ResourceStatus(
            name=config.name,
            available=False
        )
        logger.info(f"Added resource dependency: {config.name}")

    def add_managed_resource(self, config: "resource_manager.ResourceConfig"):
        """
        Add a managed resource (Docker, systemd, etc.) that will be auto-started.

        Args:
            config: Managed resource configuration from resource_manager

        Example:
            >>> from kinfra.resource_manager import get_postgres_resource
            >>> manager.add_managed_resource(get_postgres_resource(port=5432))
        """
        if not self.resource_manager:
            logger.warning("Resource management not enabled, ignoring managed resource")
            return

        self.resource_manager.add_resource(config)
        logger.info(f"Added managed resource: {config.name} ({config.type.value})")
    
    async def kill_port_processes(self, port: int) -> bool:
        """
        Kill any processes listening on the specified port.

        Args:
            port: Port number to check

        Returns:
            True if processes were killed, False otherwise
        """
        logger.info(f"Checking for processes on port {port}")

        # Run synchronous function in executor to avoid blocking
        loop = asyncio.get_event_loop()
        killed = await loop.run_in_executor(None, kill_processes_on_port, port, 5.0)

        if killed:
            # Wait a bit for port to be released
            await asyncio.sleep(1.0)

        return killed

    async def check_resource(self, name: str) -> bool:
        """
        Check if a resource is available.
        
        Args:
            name: Resource name
            
        Returns:
            True if available, False otherwise
        """
        config = self.resources.get(name)
        if not config:
            return False
        
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            result = sock.connect_ex((config.host, config.port))
            sock.close()
            
            available = result == 0
            
            self.resource_status[name] = ResourceStatus(
                name=name,
                available=available,
                last_check=datetime.now(),
                error_message=None if available else f"Connection failed to {config.host}:{config.port}"
            )
            
            return available
            
        except Exception as e:
            logger.error(f"Error checking resource {name}: {e}")
            self.resource_status[name] = ResourceStatus(
                name=name,
                available=False,
                last_check=datetime.now(),
                error_message=str(e)
            )
            return False
    
    async def check_all_resources(self) -> Dict[str, bool]:
        """
        Check all configured resources.
        
        Returns:
            Dictionary mapping resource names to availability status
        """
        if not self.resources:
            return {}
        
        results = {}
        for name in self.resources:
            available = await self.check_resource(name)
            results[name] = available
        
        return results
    
    async def start_service(self, name: str) -> bool:
        """
        Start a service with full lifecycle management.
        
        Steps:
        1. Kill any processes on the target port
        2. Allocate port via KInfra
        3. Start the service process
        4. Start Cloudflare tunnel if enabled
        5. Set up file watching if configured
        6. Perform initial health check
        
        Args:
            name: Service name
            
        Returns:
            True if started successfully
        """
        config = self.services.get(name)
        if not config:
            raise ServiceError(f"Service '{name}' not configured")
        
        status = self.service_status[name]
        status.state = "starting"
        
        logger.info(f"Starting service: {name}")
        
        # Create progress bar
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
        from rich.console import Console
        
        console = Console()
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                console=console,
                transient=True  # Remove after completion
            ) as progress:
                task = progress.add_task(f"Starting {name}...", total=7)
                
                # Step 1: Kill existing processes on port
                progress.update(task, description=f"[cyan]Checking port {config.preferred_port}...", completed=1)
                if config.preferred_port:
                    killed = await self.kill_port_processes(config.preferred_port)
                    if killed:
                        console.print(f"  ✓ Killed existing process on port {config.preferred_port}", style="yellow")
                
                # Step 2: Allocate port via KInfra
                progress.update(task, description="[cyan]Allocating port...", completed=2)
                port = self.kinfra.allocate_port(name, config.preferred_port)
                status.port = port
                logger.info(f"Allocated port {port} for {name}")
            
                # Step 3: Start fallback layer if enabled
                if self.enable_fallback_layer and config.enable_fallback and not self._fallback_started:
                    progress.update(task, description="[cyan]Starting fallback server...", completed=3)
                    await self._start_fallback_layer()

                # Step 4: Start service process
                progress.update(task, description="[cyan]Starting process...", completed=4)
                env = os.environ.copy()
                if config.env:
                    env.update(config.env)

                # Set port via environment variable (standard approach)
                env['PORT'] = str(port)

                # Use command as-is without modifying it
                command = config.command.copy()

                logger.info(f"Starting process: {' '.join(command)}")
                
                proc = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=str(config.cwd) if config.cwd else None,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                self.processes[name] = proc
                status.pid = proc.pid
                
                # Wait a bit for process to start
                await asyncio.sleep(2.0)
                
                if proc.returncode is not None:
                    # Process died immediately
                    stderr = await proc.stderr.read()
                    error_msg = stderr.decode('utf-8', errors='ignore')[:500]
                    console.print(f"\n❌ Process died immediately!", style="bold red")
                    console.print(f"Error: {error_msg}", style="red")
                    raise ServiceError(f"Process died immediately: {error_msg}")
                # Step 5: Configure fallback if enabled
                if self.enable_fallback_layer and config.enable_fallback:
                    progress.update(task, description="[cyan]Configuring fallback...", completed=5)
                    await self._configure_service_fallback(name, config, port)

                # Step 6: Start tunnel if enabled
                progress.update(task, description="[cyan]Setting up tunnel...", completed=6)
                if config.enable_tunnel:
                    logger.info(f"Starting tunnel for {name}")
                    
                    # Kill existing tunnel first
                    try:
                        await self._kill_existing_tunnel(name)
                    except Exception:
                        pass  # Ignore if no tunnel to kill
                    
                    try:
                        tunnel_info = self.kinfra.start_tunnel(
                            name,
                            port,
                            domain=config.tunnel_domain
                        )
                        status.tunnel_url = f"https://{tunnel_info.hostname}"
                        console.print(f"  ✓ Tunnel: {status.tunnel_url}", style="cyan")
                        logger.info(f"Tunnel available at: {status.tunnel_url}")
                    except Exception as e:
                        # If tunnel fails, continue without tunnel
                        error_msg = str(e)
                        if "already exists" not in error_msg.lower():
                            console.print(f"  ⚠️  Tunnel failed: {error_msg}", style="yellow")
                        logger.warning(f"Tunnel setup failed for {name}: {e}")

                # Step 7: Set up file watching
                progress.update(task, description="[cyan]Configuring watchers...", completed=7)
                if config.watch_paths and WATCHDOG_AVAILABLE:
                    self._setup_file_watching(name, config)
                elif config.watch_paths and not WATCHDOG_AVAILABLE:
                    console.print(f"  ⚠️  watchdog not installed (auto-reload disabled)", style="yellow")

                # Step 8: Perform initial health check
                progress.update(task, description="[cyan]Starting health checks...", completed=8)
                if config.health_check_url:
                    asyncio.create_task(self._check_service_health(name))
                
                # Success!
                status.state = "running"
                status.started_at = datetime.now()
                status.restart_count = 0

                # Update fallback server with running status
                if self.fallback_server:
                    self.fallback_server.update_service_status(
                        service_name=config.name,
                        status_message="Service is running",
                        port=port,
                        pid=status.pid,
                        uptime="0s",
                        health_status="Healthy",
                        state="running",
                        steps=[
                            {"text": "Allocating port", "status": "completed"},
                            {"text": "Starting process", "status": "completed"},
                            {"text": "Configuring tunnel", "status": "completed"},
                            {"text": "Health check", "status": "completed"}
                        ]
                    )

            # Show success message
            console.print(f"✅ {name} started on port {port}" +
                         (f" | PID {status.pid}" if status.pid else ""),
                         style="bold green")
            if status.tunnel_url:
                console.print(f"   {status.tunnel_url}", style="cyan")
            logger.info(f"Service {name} started successfully on port {port}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start service {name}: {e}")
            status.state = "error"
            status.error_message = str(e)
            return False
    
    async def _kill_existing_tunnel(self, name: str):
        """Kill existing cloudflare tunnel and delete it from Cloudflare."""
        import subprocess
        
        # Step 1: Kill any running cloudflared processes
        try:
            # Find all cloudflared processes
            result = subprocess.run(
                ['pgrep', '-f', 'cloudflared'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid_str in pids:
                    try:
                        pid = int(pid_str)
                        subprocess.run(['kill', '-9', str(pid)], timeout=5)
                        logger.info(f"Killed cloudflared process {pid}")
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"Error killing cloudflared processes: {e}")
        
        # Step 2: Delete the tunnel from Cloudflare
        try:
            service_slug = name.lower().replace('_', '-')
            tunnel_name = f"{service_slug}-tunnel"
            
            # List and delete existing tunnels with this name
            result = subprocess.run(
                ['cloudflared', 'tunnel', 'list', '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                tunnels = json.loads(result.stdout)
                for tunnel in tunnels:
                    if tunnel.get('name') == tunnel_name:
                        tunnel_id = tunnel.get('id')
                        logger.info(f"Deleting existing tunnel: {tunnel_name} ({tunnel_id})")
                        subprocess.run(
                            ['cloudflared', 'tunnel', 'delete', '-f', tunnel_id],
                            capture_output=True,
                            timeout=10
                        )
        except Exception as e:
            logger.debug(f"Error deleting tunnel from Cloudflare: {e}")
        
        # Wait for everything to settle
        await asyncio.sleep(2.0)
    
    def _setup_file_watching(self, name: str, config: ServiceConfig):
        """Set up file watching for auto-reload."""
        if not WATCHDOG_AVAILABLE:
            logger.warning(f"Watchdog not available, file watching disabled for {name}")
            return
        
        def on_file_change(event):
            logger.info(f"File changed for {name}: {event.src_path}")
            asyncio.create_task(self.reload_service(name))
        
        handler = FileChangeHandler(on_file_change, config.watch_patterns or ['*.py'])
        observer = Observer()
        
        for watch_path in config.watch_paths:
            if watch_path.exists():
                observer.schedule(handler, str(watch_path), recursive=True)
                logger.info(f"Watching {watch_path} for {name}")
        
        observer.start()
        self.file_observers[name] = observer
    
    async def reload_service(self, name: str) -> bool:
        """
        Reload a service (stop and start).
        
        Args:
            name: Service name
            
        Returns:
            True if reloaded successfully
        """
        logger.info(f"Reloading service: {name}")
        status = self.service_status[name]
        status.state = "reloading"
        
        await self.stop_service(name)
        await asyncio.sleep(1.0)
        return await self.start_service(name)
    
    async def _start_fallback_layer(self):
        """Start fallback server and proxy layer."""
        try:
            from .fallback_server import FallbackServer
            from .proxy_server import SmartProxyServer

            # Start fallback server
            self.fallback_server = FallbackServer(port=9000)

            # Connect fallback server to service manager for actions
            self.fallback_server.service_manager = self

            await self.fallback_server.start()
            self._fallback_started = True
            logger.info("Fallback server started on port 9000")

            # Start proxy server with fallback_server reference for status updates
            self.proxy_server = SmartProxyServer(
                proxy_port=9100,
                fallback_port=9000,
                fallback_server=self.fallback_server
            )
            await self.proxy_server.start()
            self._proxy_started = True
            logger.info("Smart proxy started on port 9100")

        except Exception as e:
            logger.warning(f"Failed to start fallback layer: {e}")
            self.enable_fallback_layer = False

    async def _configure_service_fallback(self, name: str, config: ServiceConfig, port: int):
        """Configure fallback for a specific service."""
        if not self._proxy_started or not self.fallback_server:
            return

        # Add upstream to proxy
        self.proxy_server.add_upstream(config.path_prefix, port)

        # Configure fallback page with initial status
        self.fallback_server.set_page(
            page_type=config.fallback_page,
            service_name=config.name,
            refresh_interval=config.fallback_refresh_interval,
            message=config.fallback_message
        )

        # Get service status
        status = self.service_status.get(name)
        if status:
            # Update with current service information
            self.fallback_server.update_service_status(
                service_name=config.name,
                status_message="Service is starting...",
                port=port,
                pid=status.pid,
                uptime="0s",
                health_status="Starting",
                state="starting",
                steps=[
                    {"text": "Allocating port", "status": "completed"},
                    {"text": "Starting process", "status": "active"},
                    {"text": "Configuring tunnel", "status": "pending"},
                    {"text": "Health check", "status": "pending"}
                ]
            )

        logger.info(f"Configured fallback for {name} at path {config.path_prefix}")

    async def stop_service(self, name: str) -> bool:
        """
        Stop a service gracefully.

        Args:
            name: Service name

        Returns:
            True if stopped successfully
        """
        logger.info(f"Stopping service: {name}")

        # Stop file observer
        if name in self.file_observers:
            self.file_observers[name].stop()
            self.file_observers[name].join(timeout=2)
            del self.file_observers[name]

        # Terminate process
        if name in self.processes:
            proc = self.processes[name]
            if proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Process {name} did not terminate, killing...")
                    proc.kill()
            del self.processes[name]

        # Clean up KInfra resources
        self.kinfra.cleanup(name)

        status = self.service_status[name]
        status.state = "stopped"
        status.pid = None
        status.port = None
        status.tunnel_url = None

        logger.info(f"Service {name} stopped")
        return True
    
    async def start_all(self) -> Dict[str, bool]:
        """
        Start all configured services.

        Returns:
            Dictionary mapping service names to start success status
        """
        logger.info("Starting all services")

        # Step 0: Start managed resources (Docker containers, etc.)
        if self.resource_manager and self.resource_manager.resources:
            logger.info("Starting managed system resources...")
            resource_results = await self.resource_manager.start_all()

            for resource_name, success in resource_results.items():
                if success:
                    logger.info(f"✓ Resource {resource_name} started")
                else:
                    managed_resource = self.resource_manager.resources.get(resource_name)
                    if managed_resource and managed_resource.config.required:
                        logger.error(f"Required resource {resource_name} failed to start, aborting")
                        return {service: False for service in self.services}

        # Step 1: Check resource dependencies
        logger.info("Checking resource dependencies")
        resource_results = await self.check_all_resources()

        for name, available in resource_results.items():
            config = self.resources[name]
            if config.required and not available:
                logger.error(f"Required resource '{name}' not available")
                raise ServiceError(f"Required resource '{name}' not available at {config.host}:{config.port}")
            elif not available:
                logger.warning(f"Optional resource '{name}' not available")
        
        # Start services
        results = {}
        for name in self.services:
            results[name] = await self.start_service(name)
        
        return results
    
    async def _check_service_health(self, name: str) -> bool:
        """Check service health via HTTP (both localhost and tunnel)."""
        config = self.services.get(name)
        status = self.service_status[name]

        if not config.health_check_url:
            return True

        localhost_healthy = False
        tunnel_healthy = False

        # Check localhost using utility function
        loop = asyncio.get_event_loop()
        url = config.health_check_url.format(port=status.port)
        localhost_healthy = await loop.run_in_executor(
            None, check_http_health, url, 2.0, 200, "GET"
        )

        # Check tunnel if available
        if status.tunnel_url:
            tunnel_url = f"{status.tunnel_url}/health"
            tunnel_healthy = await loop.run_in_executor(
                None, check_http_health, tunnel_url, 5.0, 200, "GET"
            )

        # Update status
        status.last_health_check = datetime.now()

        if localhost_healthy:
            if tunnel_healthy or not status.tunnel_url:
                status.health_status = "healthy"
            else:
                status.health_status = "degraded"  # Local works but tunnel doesn't
        else:
            status.health_status = "unhealthy"

        return localhost_healthy
    
    async def _monitor_service_health(self, name: str):
        """Continuously monitor service health."""
        config = self.services.get(name)
        if not config:
            return
        
        while not self._shutdown:
            await asyncio.sleep(config.health_check_interval)
            
            status = self.service_status[name]
            if status.state != "running":
                continue
            
            # Check process
            proc = self.processes.get(name)
            if proc and proc.returncode is not None:
                logger.error(f"Service {name} process died with code {proc.returncode}")
                status.state = "error"
                
                # Restart if configured
                if config.restart_on_failure and status.restart_count < config.max_restart_attempts:
                    status.restart_count += 1
                    logger.info(f"Restarting {name} (attempt {status.restart_count}/{config.max_restart_attempts})")
                    await asyncio.sleep(config.restart_delay)
                    await self.start_service(name)
                    continue
            
            # Check health endpoint
            if config.health_check_url:
                healthy = await self._check_service_health(name)
                if not healthy:
                    logger.warning(f"Health check failed for {name}")
    
    async def _monitor_resources(self):
        """Continuously monitor resource availability."""
        while not self._shutdown:
            for name, config in self.resources.items():
                await self.check_resource(name)
                await asyncio.sleep(config.check_interval / len(self.resources))
    
    async def monitor(self):
        """
        Start continuous monitoring of services and resources.
        
        This method runs until shutdown is signaled.
        """
        logger.info("Starting continuous monitoring")
        
        # Start monitoring tasks
        for name in self.services:
            task = asyncio.create_task(self._monitor_service_health(name))
            self._monitor_tasks.append(task)
        
        task = asyncio.create_task(self._monitor_resources())
        self._monitor_tasks.append(task)
        
        # Wait for shutdown
        try:
            await asyncio.sleep(float('inf'))
        except asyncio.CancelledError:
            pass
    
    async def shutdown(self):
        """Shutdown all services and cleanup."""
        logger.info("Shutting down ServiceManager")
        self._shutdown = True
        
        # Cancel monitoring tasks
        for task in self._monitor_tasks:
            task.cancel()
        await asyncio.gather(*self._monitor_tasks, return_exceptions=True)
        
        # Stop all services
        for name in list(self.services.keys()):
            await self.stop_service(name)
        
        logger.info("ServiceManager shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all services and resources.
        
        Returns:
            Dictionary with complete status information
        """
        return {
            'services': {
                name: {
                    'state': status.state,
                    'pid': status.pid,
                    'port': status.port,
                    'tunnel_url': status.tunnel_url,
                    'uptime': str(datetime.now() - status.started_at) if status.started_at else None,
                    'restart_count': status.restart_count,
                    'health_status': status.health_status,
                    'last_health_check': status.last_health_check.isoformat() if status.last_health_check else None,
                    'error_message': status.error_message
                }
                for name, status in self.service_status.items()
            },
            'resources': {
                name: {
                    'available': status.available,
                    'last_check': status.last_check.isoformat() if status.last_check else None,
                    'error_message': status.error_message
                }
                for name, status in self.resource_status.items()
            }
        }
