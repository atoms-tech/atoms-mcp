"""
Tunnel Synchronization - Automatic cloudflared tunnel management with port synchronization.

Provides intelligent tunnel lifecycle management with automatic configuration
updates, health monitoring, and seamless port changes.
"""

import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


from .exceptions import ConfigurationError, TunnelError
from .port_registry import PortRegistry
from .utils.dns import dns_safe_slug
from .utils.health import check_tunnel_health

# Try to import Cloudflare SDK for DNS management
try:
    from cloudflare import Cloudflare
    HAS_CF_SDK = True
except ImportError:
    HAS_CF_SDK = False
    Cloudflare = None

logger = logging.getLogger(__name__)

# Fallback Cloudflare API token (can be overridden via env or file)
CLOUDFLARE_API_TOKEN_FALLBACK = "F5lBjouWaymoiTgptvaWrJp-mDMLPXvHybDik_Bk"

@dataclass
class TunnelInfo:
    """Information about a tunnel configuration."""
    tunnel_id: str
    hostname: str
    config_path: str
    port: int
    process_pid: Optional[int] = None
    status: str = "unknown"  # unknown, starting, running, stopped, error
    created_at: float = 0.0
    last_health_check: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

class TunnelManager:
    """
    Intelligent tunnel manager with automatic configuration synchronization.

    Features:
    - Automatic cloudflared config generation and updates
    - Port change detection and tunnel restart
    - Health monitoring and automatic recovery
    - Process lifecycle management
    - DNS routing setup
    - Unified tunnel with path-based routing (avoids multi-level subdomain SSL issues)
    """

    def __init__(self, registry: Optional[PortRegistry] = None, domain: str = "kooshapari.com", cf_api_token: Optional[str] = None, use_unified_tunnel: bool = True, cleanup_on_start: bool = True):
        self.registry = registry or PortRegistry()
        self.domain = domain.lower()
        self.cloudflared_dir = Path.home() / ".cloudflared"
        self.cloudflared_dir.mkdir(exist_ok=True)

        # Tunnel management settings
        self.tunnel_startup_timeout = 30.0
        self.health_check_interval = 60.0
        self._running_processes: Dict[str, subprocess.Popen] = {}

        # Unified tunnel mode (recommended to avoid SSL cert issues with multi-level subdomains)
        self.use_unified_tunnel = use_unified_tunnel
        self._unified_tunnel_id: Optional[str] = None
        self._unified_config_path: Optional[Path] = None
        self._service_routes: Dict[str, Tuple[int, str]] = {}  # service_name -> (port, path)

        # Initialize Cloudflare API client if available
        self.cf_client = None
        self.cf_zone_id = None
        if HAS_CF_SDK:
            # Load token from multiple sources (in order of precedence)
            api_token = self._load_cloudflare_token(cf_api_token)

            if api_token:
                try:
                    self.cf_client = Cloudflare(api_token=api_token)
                    # Get zone ID for the domain
                    self.cf_zone_id = self._get_zone_id()
                    logger.info(f"Cloudflare API initialized for domain {self.domain}")
                except Exception as e:
                    logger.warning(f"Failed to initialize Cloudflare API: {e}")
                    logger.info("Falling back to cloudflared CLI for DNS management")
            else:
                logger.info("No CLOUDFLARE_API_TOKEN found, using cloudflared CLI for DNS")

        # Verify cloudflared availability
        self._verify_cloudflared_setup()

        # Automatic cleanup on initialization
        if cleanup_on_start and self.use_unified_tunnel:
            logger.info("Performing automatic cleanup for unified tunnel setup...")
            self._cleanup_for_unified_tunnel()

    def _load_cloudflare_token(self, explicit_token: Optional[str] = None) -> Optional[str]:
        """
        Load Cloudflare API token from multiple sources.

        Order of precedence:
        1. Explicit token passed to __init__
        2. Environment variable: CLOUDFLARE_API_TOKEN
        3. KInfra config file: ~/.kinfra/cloudflare_token
        4. Cloudflared config: ~/.cloudflared/cloudflare_token
        5. Hardcoded fallback (for kooshapari.com domain)

        Returns:
            API token string or None
        """
        # 1. Explicit token
        if explicit_token:
            logger.debug("Using explicitly provided Cloudflare token")
            return explicit_token

        # 2. Environment variable
        env_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if env_token:
            logger.debug("Using CLOUDFLARE_API_TOKEN from environment")
            return env_token

        # 3. KInfra config file
        kinfra_token_file = Path.home() / ".kinfra" / "cloudflare_token"
        if kinfra_token_file.exists():
            try:
                token = kinfra_token_file.read_text().strip()
                if token:
                    logger.debug(f"Using Cloudflare token from {kinfra_token_file}")
                    return token
            except Exception as e:
                logger.debug(f"Failed to read token from {kinfra_token_file}: {e}")

        # 4. Cloudflared directory
        cf_token_file = self.cloudflared_dir / "cloudflare_token"
        if cf_token_file.exists():
            try:
                token = cf_token_file.read_text().strip()
                if token:
                    logger.debug(f"Using Cloudflare token from {cf_token_file}")
                    return token
            except Exception as e:
                logger.debug(f"Failed to read token from {cf_token_file}: {e}")

        # 5. Fallback to hardcoded token for kooshapari.com
        if "kooshapari.com" in self.domain and CLOUDFLARE_API_TOKEN_FALLBACK:
            logger.debug("Using hardcoded fallback Cloudflare token")
            return CLOUDFLARE_API_TOKEN_FALLBACK

        logger.debug("No Cloudflare API token found")
        return None
    
    def _verify_cloudflared_setup(self):
        """Verify cloudflared is available and authenticated."""
        if not shutil.which("cloudflared"):
            raise ConfigurationError(
                "cloudflared not found. Install it with: "
                "https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
            )

        cert_path = self.cloudflared_dir / "cert.pem"
        if not cert_path.exists():
            raise ConfigurationError(
                "cloudflared not authenticated. Run: cloudflared tunnel login"
            )

    def _cleanup_for_unified_tunnel(self):
        """
        Comprehensive cleanup before setting up unified tunnel.

        Steps:
        1. Stop all running cloudflared processes
        2. List existing tunnels and identify stale ones
        3. Clean up DNS records for the domain
        4. Remove old config files
        """
        logger.info(f"Starting cleanup for unified tunnel on domain: {self.domain}")

        # 1. Stop all running cloudflared processes
        logger.info("Stopping all running cloudflared processes...")
        self._stop_all_cloudflared_processes()

        # 2. List existing tunnels (for informational purposes)
        logger.info("Listing existing Cloudflare tunnels...")
        existing_tunnels = self._list_all_tunnels()
        if existing_tunnels:
            logger.info(f"Found {len(existing_tunnels)} existing tunnel(s):")
            for tunnel in existing_tunnels:
                logger.info(f"  - {tunnel.get('name')} (ID: {tunnel.get('id')})")

        # 3. Clean up DNS records for the domain
        logger.info(f"Cleaning up DNS records for domain: {self.domain}")
        self._cleanup_dns_records()

        # 4. Clean up old config files for this domain
        logger.info("Cleaning up old config files...")
        self._cleanup_old_configs()

        logger.info("Cleanup complete. Ready for unified tunnel setup.")

    def _stop_all_cloudflared_processes(self):
        """Stop all running cloudflared processes."""
        try:
            # Find all cloudflared processes
            result = subprocess.run(
                ["pgrep", "-f", "cloudflared"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                logger.info(f"Found {len(pids)} cloudflared process(es) to stop")

                for pid in pids:
                    try:
                        logger.debug(f"Stopping cloudflared process PID: {pid}")
                        subprocess.run(["kill", pid], timeout=2)
                    except Exception as e:
                        logger.debug(f"Could not stop process {pid}: {e}")

                # Wait a moment for processes to terminate
                time.sleep(2)

                # Force kill any remaining processes
                result = subprocess.run(
                    ["pgrep", "-f", "cloudflared"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    remaining_pids = result.stdout.strip().split('\n')
                    logger.warning(f"Force killing {len(remaining_pids)} remaining process(es)")
                    for pid in remaining_pids:
                        try:
                            subprocess.run(["kill", "-9", pid], timeout=2)
                        except Exception as e:
                            logger.debug(f"Could not force kill process {pid}: {e}")

                logger.info("All cloudflared processes stopped")
            else:
                logger.info("No running cloudflared processes found")

        except subprocess.TimeoutExpired:
            logger.warning("Timeout while stopping cloudflared processes")
        except Exception as e:
            logger.warning(f"Error stopping cloudflared processes: {e}")

    def _list_all_tunnels(self) -> List[Dict]:
        """List all existing Cloudflare tunnels."""
        try:
            result = subprocess.run(
                ["cloudflared", "tunnel", "list", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                tunnels = json.loads(result.stdout)
                return tunnels if isinstance(tunnels, list) else []
        except (subprocess.TimeoutExpired, json.JSONDecodeError, subprocess.SubprocessError) as e:
            logger.warning(f"Failed to list tunnels: {e}")

        return []

    def _cleanup_dns_records(self):
        """Delete all DNS records (A, AAAA, CNAME) for the domain."""
        if self.cf_client and self.cf_zone_id:
            try:
                self._cleanup_dns_via_api()
                return
            except Exception as e:
                logger.warning(f"API DNS cleanup failed: {e}")

        logger.info("Cannot cleanup DNS records without Cloudflare API access")
        logger.info("You may need to manually remove old DNS records from Cloudflare dashboard")

    def _cleanup_dns_via_api(self):
        """Delete DNS records using Cloudflare API."""
        if not self.cf_client or not self.cf_zone_id:
            return

        deleted_count = 0
        record_types = ["A", "AAAA", "CNAME"]

        for record_type in record_types:
            try:
                records = self.cf_client.dns.records.list(
                    zone_id=self.cf_zone_id,
                    name=self.domain,
                    type=record_type
                )

                for record in records.result:
                    if record.name == self.domain:
                        logger.info(f"Deleting {record_type} record: {self.domain} -> {record.content}")
                        self.cf_client.dns.records.delete(
                            dns_record_id=record.id,
                            zone_id=self.cf_zone_id
                        )
                        deleted_count += 1
                        time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.debug(f"Error cleaning up {record_type} records: {e}")

        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} DNS record(s) for {self.domain}")
        else:
            logger.info(f"No existing DNS records found for {self.domain}")

    def _cleanup_old_configs(self):
        """Remove old config files for this domain."""
        domain_prefix = self.domain.split('.')[0]
        pattern = f"config-{domain_prefix}*.yml"

        deleted_count = 0
        for config_file in self.cloudflared_dir.glob(pattern):
            try:
                logger.debug(f"Removing old config: {config_file}")
                config_file.unlink()
                deleted_count += 1
            except Exception as e:
                logger.debug(f"Could not remove {config_file}: {e}")

        if deleted_count > 0:
            logger.info(f"Removed {deleted_count} old config file(s)")
        else:
            logger.debug("No old config files to remove")
    
    def start_tunnel(self, service_name: str, port: int, path: str = "/") -> TunnelInfo:
        """
        Start or update a tunnel for a service.

        In unified mode: Adds service to shared tunnel with path-based routing
        In separate mode: Creates individual tunnel per service

        Args:
            service_name: Name of the service
            port: Local port to tunnel to
            path: URL path for this service (e.g., "/api", "/")

        Returns:
            TunnelInfo object with tunnel details
        """
        logger.info(f"Starting tunnel for service '{service_name}' on port {port}, path '{path}'")

        if self.use_unified_tunnel:
            return self._start_unified_tunnel_service(service_name, port, path)
        else:
            return self._start_separate_tunnel(service_name, port)

    def _start_unified_tunnel_service(self, service_name: str, port: int, path: str) -> TunnelInfo:
        """
        Add service to unified tunnel with path-based routing.

        This method:
        1. Creates or finds the unified tunnel (once)
        2. Sets up DNS for the main domain (once)
        3. Adds the service to the routing table
        4. Regenerates the config with all services
        5. Restarts the tunnel process
        """
        logger.info(f"Adding service '{service_name}' to unified tunnel: port={port}, path='{path}'")

        # Add or update service route
        self._service_routes[service_name] = (port, path)

        # Create or find unified tunnel (only once)
        if not self._unified_tunnel_id:
            tunnel_name = f"{self.domain.split('.')[0]}-unified"
            logger.info(f"Initializing unified tunnel: {tunnel_name}")

            # Try to find existing tunnel
            self._unified_tunnel_id = self._find_existing_tunnel(tunnel_name)

            if self._unified_tunnel_id:
                logger.info(f"Found existing tunnel '{tunnel_name}' with ID: {self._unified_tunnel_id}")
            else:
                logger.info(f"Creating new tunnel '{tunnel_name}'")
                self._unified_tunnel_id = self._create_cloudflare_tunnel(tunnel_name)
                logger.info(f"Created tunnel '{tunnel_name}' with ID: {self._unified_tunnel_id}")

            # Set up DNS for main domain (only once)
            logger.info(f"Setting up DNS for domain: {self.domain}")
            self._setup_dns_route(self._unified_tunnel_id, self.domain)
            logger.info(f"DNS configured: {self.domain} -> tunnel {self._unified_tunnel_id}")

        # Regenerate unified config with all services
        logger.info(f"Generating unified config with {len(self._service_routes)} service(s)")
        self._unified_config_path = self._generate_unified_config()

        # Restart tunnel process with updated config
        if "unified" in self._running_processes:
            logger.info("Restarting unified tunnel process with updated configuration")
            self._stop_tunnel_process("unified")
        else:
            logger.info("Starting unified tunnel process")

        self._start_tunnel_process("unified", self._unified_config_path)

        # Update service registry
        self.registry.update_service(
            service_name,
            tunnel_id=self._unified_tunnel_id,
            tunnel_hostname=self.domain,
            config_path=str(self._unified_config_path)
        )

        logger.info(f"Service '{service_name}' added to unified tunnel successfully")
        logger.info(f"Service URL: https://{self.domain}{path}")

        return TunnelInfo(
            tunnel_id=self._unified_tunnel_id,
            hostname=self.domain,
            config_path=str(self._unified_config_path),
            port=port,
            status="running"
        )

    def _start_separate_tunnel(self, service_name: str, port: int) -> TunnelInfo:
        """Start individual tunnel for a service (old method)."""
        service_slug = dns_safe_slug(service_name)
        hostname = f"{service_slug}.{self.domain}"

        # Check if tunnel already exists and needs update
        service_info = self.registry.get_service(service_name)
        if service_info and service_info.tunnel_id:
            if service_info.assigned_port != port:
                logger.info(f"Port changed for '{service_name}': {service_info.assigned_port} -> {port}")
                return self._update_tunnel_port(service_name, service_info.tunnel_id, hostname, port)
            else:
                # Check if tunnel is still running
                if self._is_tunnel_running(service_info.tunnel_id, hostname):
                    logger.info(f"Tunnel for '{service_name}' already running")
                    return TunnelInfo(
                        tunnel_id=service_info.tunnel_id,
                        hostname=hostname,
                        config_path=service_info.config_path or "",
                        port=port,
                        status="running"
                    )

        # Create new tunnel
        return self._create_tunnel(service_name, service_slug, hostname, port)
    
    def _create_tunnel(self, service_name: str, service_slug: str, hostname: str, port: int) -> TunnelInfo:
        """Create a new tunnel for the service."""
        logger.info(f"Creating new tunnel: {hostname} -> localhost:{port}")
        
        # Generate tunnel name
        tunnel_name = f"{service_slug}-tunnel"
        
        # Check if tunnel already exists in cloudflare
        tunnel_id = self._find_existing_tunnel(tunnel_name)
        if not tunnel_id:
            tunnel_id = self._create_cloudflare_tunnel(tunnel_name)
        
        # Set up DNS routing
        self._setup_dns_route(tunnel_id, hostname)
        
        # Generate configuration
        config_path = self._generate_tunnel_config(service_slug, tunnel_id, hostname, port)
        
        # Start tunnel process
        self._start_tunnel_process(service_name, config_path)
        
        # Update service registry
        self.registry.update_service(
            service_name,
            tunnel_id=tunnel_id,
            tunnel_hostname=hostname,
            config_path=str(config_path)
        )
        
        tunnel_info = TunnelInfo(
            tunnel_id=tunnel_id,
            hostname=hostname,
            config_path=str(config_path),
            port=port,
            status="starting"
        )
        
        logger.info(f"Tunnel created: {hostname}")
        return tunnel_info
    
    def _update_tunnel_port(self, service_name: str, tunnel_id: str, hostname: str, new_port: int) -> TunnelInfo:
        """Update tunnel configuration for port change."""
        logger.info(f"Updating tunnel port for '{service_name}': {hostname} -> localhost:{new_port}")
        
        # Stop existing tunnel
        self._stop_tunnel_process(service_name)
        
        # Update configuration
        service_slug = hostname.split('.')[0]  # Extract slug from hostname
        config_path = self._generate_tunnel_config(service_slug, tunnel_id, hostname, new_port)
        
        # Start tunnel with new config
        self._start_tunnel_process(service_name, config_path)
        
        # Update registry
        self.registry.update_service(
            service_name,
            config_path=str(config_path)
        )
        
        return TunnelInfo(
            tunnel_id=tunnel_id,
            hostname=hostname,
            config_path=str(config_path),
            port=new_port,
            status="starting"
        )
    
    def _find_existing_tunnel(self, tunnel_name: str) -> Optional[str]:
        """Find existing cloudflare tunnel by name."""
        try:
            result = subprocess.run(
                ["cloudflared", "tunnel", "list", "--output", "json"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                tunnels = json.loads(result.stdout)
                for tunnel in tunnels:
                    if tunnel.get("name") == tunnel_name:
                        return tunnel.get("id")
        except (subprocess.TimeoutExpired, json.JSONDecodeError, subprocess.SubprocessError) as e:
            logger.warning(f"Failed to list tunnels: {e}")
        
        return None
    
    def _create_cloudflare_tunnel(self, tunnel_name: str) -> str:
        """Create a new cloudflare tunnel."""
        logger.info(f"Creating cloudflare tunnel: {tunnel_name}")
        
        try:
            result = subprocess.run(
                ["cloudflared", "tunnel", "create", tunnel_name],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                raise TunnelError(f"Failed to create tunnel '{tunnel_name}': {result.stderr}")
            
            # Extract tunnel ID from output
            # Output format: "Created tunnel <name> with id <id>"
            tunnel_id = self._find_existing_tunnel(tunnel_name)
            if not tunnel_id:
                raise TunnelError(f"Tunnel '{tunnel_name}' created but ID not found")
            
            logger.info(f"Created tunnel '{tunnel_name}' with ID: {tunnel_id}")
            return tunnel_id
            
        except subprocess.TimeoutExpired:
            raise TunnelError(f"Timeout creating tunnel '{tunnel_name}'")
    
    def _get_zone_id(self) -> Optional[str]:
        """Get Cloudflare zone ID for the domain."""
        if not self.cf_client:
            return None

        try:
            # Extract root domain (e.g., byte.kooshapari.com -> kooshapari.com)
            parts = self.domain.split('.')
            root_domain = '.'.join(parts[-2:]) if len(parts) > 2 else self.domain

            logger.debug(f"Looking up zone for root domain: {root_domain}")
            zones = self.cf_client.zones.list(name=root_domain)

            if zones and len(zones.result) > 0:
                zone_id = zones.result[0].id
                logger.debug(f"Found zone ID for {root_domain}: {zone_id}")

                # Configure SSL settings for tunnel compatibility
                self._configure_ssl_for_tunnels(zone_id)

                return zone_id
        except Exception as e:
            logger.warning(f"Failed to get zone ID: {e}")

        return None

    def _configure_ssl_for_tunnels(self, zone_id: str):
        """Configure SSL/TLS settings for optimal tunnel compatibility."""
        if not self.cf_client:
            return

        try:
            # Set SSL mode to Full (not Full Strict) for tunnel compatibility
            # Full mode: Encrypts traffic between Cloudflare and origin, but doesn't validate cert
            current_ssl = self.cf_client.zones.settings.get(zone_id=zone_id, setting_id="ssl")

            if current_ssl.value != "full":
                logger.info(f"Updating SSL mode from '{current_ssl.value}' to 'full' for tunnel compatibility")
                self.cf_client.zones.settings.edit(
                    zone_id=zone_id,
                    setting_id="ssl",
                    value="full"
                )
                logger.info("✓ SSL mode set to 'full'")

            # Enable TLS 1.3 for better performance
            try:
                self.cf_client.zones.settings.edit(
                    zone_id=zone_id,
                    setting_id="tls_1_3",
                    value="on"
                )
                logger.debug("✓ TLS 1.3 enabled")
            except Exception:
                pass

            # Set minimum TLS version to 1.2 (compatible with most clients)
            try:
                self.cf_client.zones.settings.edit(
                    zone_id=zone_id,
                    setting_id="min_tls_version",
                    value="1.2"
                )
                logger.debug("✓ Minimum TLS version set to 1.2")
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Could not configure SSL settings: {e}")
            logger.info("You may need to manually set SSL/TLS mode to 'Full' in Cloudflare dashboard")

    def _setup_dns_route(self, tunnel_id: str, hostname: str):
        """Set up DNS routing for the tunnel using Cloudflare API."""
        logger.info(f"Setting up DNS route: {hostname} -> tunnel {tunnel_id}")

        # Use Cloudflare API if available
        if self.cf_client and self.cf_zone_id:
            try:
                self._setup_dns_via_api(tunnel_id, hostname)
                return
            except Exception as e:
                logger.warning(f"API DNS setup failed: {e}, falling back to CLI")

        # Fallback to cloudflared CLI
        self._setup_dns_via_cli(tunnel_id, hostname)

    def _setup_dns_via_api(self, tunnel_id: str, hostname: str):
        """
        Set up DNS using Cloudflare API (preferred method).

        Steps:
        1. Delete ALL existing DNS records (A, AAAA, CNAME) for the hostname
        2. Create new CNAME record pointing to the tunnel
        3. Verify DNS record was created successfully
        """
        if not self.cf_client or not self.cf_zone_id:
            raise TunnelError("Cloudflare API client not initialized")

        # Delete ALL existing DNS records for the hostname
        logger.info(f"Cleaning up existing DNS records for: {hostname}")
        deleted_count = 0
        record_types = ["A", "AAAA", "CNAME"]

        for record_type in record_types:
            try:
                records = self.cf_client.dns.records.list(
                    zone_id=self.cf_zone_id,
                    name=hostname,
                    type=record_type
                )

                for record in records.result:
                    if record.name == hostname:
                        logger.info(f"Deleting existing {record_type} record: {hostname} -> {record.content}")
                        self.cf_client.dns.records.delete(
                            dns_record_id=record.id,
                            zone_id=self.cf_zone_id
                        )
                        deleted_count += 1
                        time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.debug(f"Error cleaning up {record_type} records: {e}")

        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} existing DNS record(s)")
            time.sleep(2)  # Wait for deletions to propagate

        # Create CNAME record pointing to tunnel
        cname_target = f"{tunnel_id}.cfargotunnel.com"
        logger.info(f"Creating CNAME record: {hostname} -> {cname_target}")

        try:
            record = self.cf_client.dns.records.create(
                zone_id=self.cf_zone_id,
                name=hostname,
                type="CNAME",
                content=cname_target,
                proxied=True,  # Enable Cloudflare proxy
                ttl=1  # Automatic TTL
            )
            logger.info(f"✓ DNS record created successfully: {hostname} -> {cname_target}")
            logger.info(f"  Record ID: {record.id}, Proxied: {record.proxied}")

            # Verify the record was created
            time.sleep(1)
            verify_records = self.cf_client.dns.records.list(
                zone_id=self.cf_zone_id,
                name=hostname,
                type="CNAME"
            )

            verified = False
            for verify_record in verify_records.result:
                if verify_record.name == hostname and verify_record.content == cname_target:
                    verified = True
                    logger.info("✓ DNS record verified in Cloudflare")
                    break

            if not verified:
                logger.warning("DNS record created but verification failed")

        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                logger.warning(f"DNS record already exists: {hostname}")
            else:
                raise TunnelError(f"Failed to create DNS record: {e}")

    def _setup_dns_via_cli(self, tunnel_id: str, hostname: str):
        """Set up DNS using cloudflared CLI (fallback method)."""
        try:
            result = subprocess.run(
                ["cloudflared", "tunnel", "route", "dns", tunnel_id, hostname],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode != 0:
                stderr = result.stderr.lower()
                if "already exists" not in stderr and "duplicate" not in stderr:
                    logger.warning(f"DNS route setup warning: {result.stderr}")
            else:
                logger.info(f"✓ DNS route configured via CLI: {hostname}")

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout setting up DNS route for {hostname}")
    
    def _generate_tunnel_config(self, service_slug: str, tunnel_id: str, hostname: str, port: int) -> Path:
        """Generate cloudflared configuration file."""
        config_path = self.cloudflared_dir / f"config-{service_slug}.yml"
        creds_file = self.cloudflared_dir / f"{tunnel_id}.json"

        # IMPORTANT: Order matters! tunnel must be first for proper SSL handling
        # Write config manually to ensure correct order
        config_content = f"""tunnel: {tunnel_id}
credentials-file: {creds_file}

ingress:
  - hostname: {hostname}
    service: http://127.0.0.1:{port}
  - service: http_status:404
"""

        # Write config file
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        logger.debug(f"Generated tunnel config: {config_path}")
        return config_path
    
    def _start_tunnel_process(self, service_name: str, config_path: Path):
        """Start the cloudflared tunnel process."""
        logger.info(f"Starting tunnel process for '{service_name}' with config: {config_path}")
        
        # Stop existing process if running
        self._stop_tunnel_process(service_name)
        
        try:
            # Start cloudflared process
            process = subprocess.Popen(
                ["cloudflared", "tunnel", "--config", str(config_path), "run"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self._running_processes[service_name] = process
            logger.info(f"Started tunnel process for '{service_name}' (PID: {process.pid})")
            
            # Update service registry with process info
            self.registry.update_service(service_name, pid=process.pid)
            
        except OSError as e:
            raise TunnelError(f"Failed to start tunnel process for '{service_name}': {e}")
    
    def _stop_tunnel_process(self, service_name: str) -> bool:
        """Stop the tunnel process for a service."""
        if service_name in self._running_processes:
            process = self._running_processes[service_name]
            logger.info(f"Stopping tunnel process for '{service_name}' (PID: {process.pid})")
            
            try:
                process.terminate()
                process.wait(timeout=5.0)
                del self._running_processes[service_name]
                logger.info(f"Tunnel process for '{service_name}' stopped gracefully")
                return True
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing tunnel process for '{service_name}'")
                process.kill()
                process.wait()
                del self._running_processes[service_name]
                return True
            except Exception as e:
                logger.error(f"Error stopping tunnel process for '{service_name}': {e}")
                return False
        
        return False
    
    def _is_tunnel_running(self, tunnel_id: str, hostname: str) -> bool:
        """Check if a tunnel is currently running."""
        # Check if we have a process tracked for this tunnel
        for service_name, process in self._running_processes.items():
            if process and process.poll() is None:  # Process exists and is alive
                service_info = self.registry.get_service(service_name)
                if service_info and service_info.tunnel_id == tunnel_id:
                    logger.debug(f"Tunnel {tunnel_id} is running (PID: {process.pid})")
                    return True

        # Fallback: Check if any cloudflared process is running with this config
        try:
            result = subprocess.run(
                ["pgrep", "-f", f"cloudflared.*{tunnel_id}"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                logger.debug(f"Found cloudflared process for tunnel {tunnel_id}")
                return True
        except Exception as e:
            logger.debug(f"Error checking for cloudflared process: {e}")

        logger.debug(f"Tunnel {tunnel_id} is NOT running")
        return False
    
    def stop_tunnel(self, service_name: str) -> bool:
        """Stop the tunnel for a service."""
        logger.info(f"Stopping tunnel for service '{service_name}'")
        
        success = self._stop_tunnel_process(service_name)
        
        # Clear tunnel info from registry
        self.registry.update_service(
            service_name,
            tunnel_id=None,
            tunnel_hostname=None,
            config_path=None,
            pid=None
        )
        
        return success
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get the public URL for a service."""
        service_info = self.registry.get_service(service_name)
        if service_info and service_info.tunnel_hostname:
            return f"https://{service_info.tunnel_hostname}"
        return None
    
    def get_tunnel_status(self, service_name: str) -> Dict:
        """Get detailed tunnel status for a service."""
        service_info = self.registry.get_service(service_name)
        if not service_info:
            return {"status": "not_found", "message": f"Service '{service_name}' not found"}

        status = {
            "service_name": service_name,
            "port": service_info.assigned_port,
            "tunnel_id": service_info.tunnel_id,
            "hostname": service_info.tunnel_hostname,
            "url": f"https://{service_info.tunnel_hostname}" if service_info.tunnel_hostname else None,
            "process_running": service_name in self._running_processes,
            "last_seen": service_info.last_seen
        }

        if service_info.tunnel_id:
            status["tunnel_running"] = self._is_tunnel_running(service_info.tunnel_id, service_info.tunnel_hostname)

            # Add health check
            if status["tunnel_running"]:
                status["tunnel_healthy"] = check_tunnel_health(service_info.tunnel_hostname, service_info.assigned_port)

        return status
    
    def cleanup_all(self):
        """Clean up all running tunnel processes."""
        logger.info("Cleaning up all tunnel processes")
        
        for service_name in list(self._running_processes.keys()):
            self._stop_tunnel_process(service_name)

        self._running_processes.clear()

    def _generate_unified_config(self) -> Path:
        """Generate unified tunnel config with all services using path-based routing."""
        config_path = self.cloudflared_dir / f"config-{self.domain.split('.')[0]}.yml"
        creds_file = self.cloudflared_dir / f"{self._unified_tunnel_id}.json"

        # Build ingress rules - services with specific paths first, then catch-all
        ingress_rules = []

        # Sort by path specificity (more specific paths first)
        sorted_services = sorted(
            self._service_routes.items(),
            key=lambda x: (0 if x[1][1] != "/" else 1, len(x[1][1])),
            reverse=True
        )

        for service_name, (port, path) in sorted_services:
            if path != "/":
                # Specific path - add wildcard for subpaths
                ingress_rules.append({
                    'hostname': self.domain,
                    'path': f"{path}/*",
                    'service': f'http://127.0.0.1:{port}'
                })

        # Add root path services last (catch-all for that hostname)
        for service_name, (port, path) in self._service_routes.items():
            if path == "/":
                ingress_rules.append({
                    'hostname': self.domain,
                    'service': f'http://127.0.0.1:{port}'
                })

        # Final catch-all 404
        ingress_rules.append({'service': 'http_status:404'})

        # Write config with correct order (tunnel first!)
        config_content = f"""tunnel: {self._unified_tunnel_id}
credentials-file: {creds_file}

ingress:
"""
        for rule in ingress_rules:
            config_content += "  - "
            if 'hostname' in rule:
                config_content += f"hostname: {rule['hostname']}\n"
                if 'path' in rule:
                    config_content += f"    path: {rule['path']}\n"
                config_content += f"    service: {rule['service']}\n"
            else:
                config_content += f"service: {rule['service']}\n"

        with open(config_path, 'w') as f:
            f.write(config_content)

        logger.info(f"Generated unified tunnel config with {len(self._service_routes)} services")
        logger.debug(f"Config: {config_path}")

        return config_path
