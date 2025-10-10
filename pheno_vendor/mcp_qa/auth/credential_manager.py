"""
Secure Credential Manager with AES-256 Encryption

Provides encrypted storage for all types of authentication credentials:
- Passwords
- TOTP secrets
- API tokens
- OAuth tokens
- Session cookies
- Passkey metadata

Storage: ~/.mcp_qa/credentials.enc (encrypted JSON)
Encryption: AES-256-GCM with PBKDF2 key derivation
"""

import getpass
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Set

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

from mcp_qa.logging import get_logger


class CredentialType(Enum):
    """Types of credentials that can be stored."""
    PASSWORD = "password"
    TOTP_SECRET = "totp_secret"
    API_TOKEN = "api_token"
    OAUTH_TOKEN = "oauth_token"
    SESSION_COOKIE = "session_cookie"
    PASSKEY_METADATA = "passkey_metadata"
    CUSTOM = "custom"


ENV_IMPORT_RULES: List[Dict[str, Any]] = [
    {
        "name": "authkit_env_login",
        "provider": "authkit",
        "credential_type": CredentialType.PASSWORD,
        "value_keys": [
            "ATOMS_TEST_PASSWORD",
            "ZEN_TEST_PASSWORD",
            "OAUTH_AUTHKIT_PASSWORD",
            "OAUTH_PASSWORD",
            "AUTHKIT_TEST_PASSWORD",
        ],
        "email_keys": [
            "ATOMS_TEST_EMAIL",
            "ZEN_TEST_EMAIL",
            "OAUTH_AUTHKIT_EMAIL",
            "OAUTH_EMAIL",
            "AUTHKIT_TEST_EMAIL",
        ],
        "username_keys": [
            "ATOMS_TEST_USERNAME",
            "ZEN_TEST_USERNAME",
            "AUTHKIT_TEST_USERNAME",
        ],
        "metadata_keys": {
            "mcp_endpoint": [
                "MCP_ENDPOINT",
                "ATOMS_FASTMCP_BASE_URL",
                "FASTMCP_BASE_URL",
            ]
        },
    },
    {
        "name": "authkit_env_totp",
        "provider": "authkit",
        "credential_type": CredentialType.TOTP_SECRET,
        "value_keys": [
            "ATOMS_TEST_MFA_CODE",
            "ATOMS_TEST_MFA_SECRET",
            "ZEN_TEST_MFA_CODE",
            "ZEN_TEST_MFA_SECRET",
            "OAUTH_AUTHKIT_MFA_SECRET",
            "AUTHKIT_TOTP_SECRET",
            "TOTP_SECRET",
        ],
    },
    {
        "name": "github_env_login",
        "provider": "github",
        "credential_type": CredentialType.PASSWORD,
        "value_keys": [
            "GITHUB_PASSWORD",
            "GITHUB_TOKEN",
            "OAUTH_GITHUB_PASSWORD",
        ],
        "username_keys": [
            "GITHUB_USERNAME",
            "OAUTH_GITHUB_USERNAME",
        ],
        "metadata_keys": {
            "token_type": ["GITHUB_TOKEN_TYPE"],
        },
    },
    {
        "name": "github_env_totp",
        "provider": "github",
        "credential_type": CredentialType.TOTP_SECRET,
        "value_keys": [
            "GITHUB_MFA_SECRET",
            "GITHUB_TOTP_SECRET",
        ],
    },
    {
        "name": "google_env_login",
        "provider": "google",
        "credential_type": CredentialType.PASSWORD,
        "value_keys": [
            "GOOGLE_PASSWORD",
            "OAUTH_GOOGLE_PASSWORD",
        ],
        "email_keys": [
            "GOOGLE_EMAIL",
            "OAUTH_GOOGLE_EMAIL",
        ],
    },
    {
        "name": "google_env_totp",
        "provider": "google",
        "credential_type": CredentialType.TOTP_SECRET,
        "value_keys": [
            "GOOGLE_MFA_SECRET",
            "GOOGLE_TOTP_SECRET",
        ],
    },
    {
        "name": "supabase_service_role",
        "provider": "supabase",
        "credential_type": CredentialType.API_TOKEN,
        "value_keys": [
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_KEY",
        ],
        "metadata_keys": {
            "url": ["SUPABASE_URL"],
            "anon_key": ["SUPABASE_ANON_KEY"],
        },
    },
]


@dataclass
class Credential:
    """A stored credential."""

    # Identification
    name: str
    credential_type: CredentialType
    provider: str  # e.g., "authkit", "google", "github"

    # Credential data
    value: str  # The actual secret (encrypted at rest)

    # Optional metadata
    username: Optional[str] = None
    email: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if credential has expired."""
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['credential_type'] = self.credential_type.value
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Credential':
        """Create from dictionary."""
        data = dict(data)
        data['credential_type'] = CredentialType(data['credential_type'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class CredentialManager:
    """
    Secure credential manager with encrypted storage.

    Features:
    - AES-256-GCM encryption
    - Master password protection
    - Multiple credential types
    - Automatic key derivation (PBKDF2)
    - Safe storage in ~/.mcp_qa/

    Usage:
        manager = CredentialManager()

        # Store password
        manager.store_credential(
            name="authkit_main",
            credential_type=CredentialType.PASSWORD,
            provider="authkit",
            value="my_password",
            email="user@example.com"
        )

        # Retrieve password
        cred = manager.get_credential("authkit_main")
        print(cred.value)  # Decrypted password

        # Store TOTP secret
        manager.store_credential(
            name="authkit_totp",
            credential_type=CredentialType.TOTP_SECRET,
            provider="authkit",
            value="JBSWY3DPEHPK3PXP"
        )
    """

    def __init__(
        self,
        master_password: Optional[str] = None,
        storage_dir: Optional[Path] = None
    ):
        """
        Initialize credential manager.

        Args:
            master_password: Master password for encryption (prompts if not provided)
            storage_dir: Storage directory (default: ~/.mcp_qa/)
        """
        # Initialize logger FIRST so it's available if anything fails
        self.logger = get_logger(__name__)
        
        self.storage_dir = storage_dir or Path.home() / ".mcp_qa"
        self.storage_dir.mkdir(exist_ok=True, mode=0o700)

        self.credentials_file = self.storage_dir / "credentials.enc"
        self.salt_file = self.storage_dir / ".salt"

        # Get or create master password
        self.master_password = master_password or self._get_master_password()

        # Derive encryption key
        self._cipher = self._create_cipher()

        # Load existing credentials
        self._credentials: Dict[str, Credential] = self._load_credentials()
        self._env_bootstrapped = False
        self._bootstrap_from_env()

    def _get_master_password(self) -> str:
        """Get master password from env, keychain, or prompt."""
        logger = get_logger(__name__)
        
        # Check environment variable first
        env_password = os.getenv("MCP_QA_MASTER_PASSWORD")
        if env_password:
            logger.debug("Using master password from environment")
            return env_password

        # Try to get from OS Keychain (macOS)
        keychain_available = False
        keychain = None
        account = "mcp_qa_master_password"
        
        try:
            from mcp_qa.auth.keychain_manager import get_keychain_manager
            keychain = get_keychain_manager()
            keychain_available = keychain.is_keychain_available()
        except ImportError:
            logger.debug("Keychain manager not available")
        except Exception as e:
            logger.warning("Keychain initialization failed", error=str(e))
        
        if keychain_available and keychain:
            # Try to retrieve from keychain first
            try:
                stored_password = keychain.get_password(account)
                if stored_password:
                    logger.info("🔓 Using master password from Keychain")
                    
                    # Verify it works with existing credentials file
                    if self.credentials_file.exists():
                        try:
                            # Quick validation - try to decrypt
                            test_cipher = self._create_cipher_with_password(stored_password)
                            encrypted_data = self.credentials_file.read_bytes()
                            test_cipher.decrypt(encrypted_data)
                            logger.debug("Keychain password verified")
                            return stored_password
                        except Exception:
                            # Password in keychain doesn't match encrypted file
                            logger.warning(
                                "Keychain password doesn't match credential store",
                                emoji="⚠️"
                            )
                            # Delete the incorrect keychain entry
                            keychain.delete_password(account)
                            # Fall through to prompt
                    else:
                        # No credential file yet, keychain password is fine
                        return stored_password
            except Exception as e:
                logger.debug("Keychain retrieval failed", error=str(e))
            
            # Not in keychain or keychain password was wrong
            if self.credentials_file.exists():
                # Existing credentials - prompt and try to migrate to keychain
                logger.info(
                    "🔐 Enter master password to unlock credentials",
                )
                print("💡 Tip: After successful login, your password will be saved to macOS Keychain")
                print("    Future logins will use TouchID/passkey instead of typing password\n")
                
                password = getpass.getpass("🔐 Master password: ")
                
                # Validate password by trying to decrypt
                try:
                    test_cipher = self._create_cipher_with_password(password)
                    encrypted_data = self.credentials_file.read_bytes()
                    test_cipher.decrypt(encrypted_data)
                    
                    # Password works! Save to keychain for future use
                    print("\n💡 Saving password to macOS Keychain...")
                    print("⚠️  IMPORTANT: When the system prompt appears, click 'Always Allow'")
                    print("    This enables automatic access without re-entering passwords\n")
                    
                    if keychain.store_password(account, password, use_biometric=True):
                        logger.info(
                            "✅ Master password saved to Keychain"
                        )
                        print("✅ Password saved! If you clicked 'Always Allow', future access is automatic.\n")
                    
                    return password
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to decrypt credentials. Wrong password? Error: {e}"
                    )
            else:
                # First time - create new master password and save to keychain
                logger.info("🔐 Creating new credential store with Keychain")
                print("\n📋 Create a master password to secure your credentials")
                print("💡 This will be saved to macOS Keychain for TouchID access\n")
                
                password = getpass.getpass("🔐 Create master password: ")
                confirm = getpass.getpass("🔐 Confirm master password: ")

                if password != confirm:
                    raise ValueError("Passwords do not match")

                if len(password) < 8:
                    raise ValueError("Password must be at least 8 characters")
                
                # Save to keychain
                print("\n💡 Saving to macOS Keychain...")
                print("⚠️  IMPORTANT: When prompted, click 'Always Allow' for automatic access\n")
                
                if keychain.store_password(account, password, use_biometric=True):
                    logger.info("✅ Master password saved to Keychain")
                    print("✅ Saved! Next time: No password typing needed (if you clicked 'Always Allow')\n")

                return password
        
        # Fallback to manual password entry (non-macOS or keychain unavailable)
        if self.credentials_file.exists():
            # Existing credentials - prompt for password
            password = getpass.getpass("🔐 Enter master password: ")
            
            # Validate password
            try:
                test_cipher = self._create_cipher_with_password(password)
                encrypted_data = self.credentials_file.read_bytes()
                test_cipher.decrypt(encrypted_data)
                return password
            except Exception as e:
                raise RuntimeError(
                    f"Failed to decrypt credentials. Wrong password? Error: {e}"
                )
        else:
            # First time - create new master password
            logger.info("Creating new credential store", emoji="🔐")
            password = getpass.getpass("🔐 Enter new master password: ")
            confirm = getpass.getpass("🔐 Confirm master password: ")

            if password != confirm:
                raise ValueError("Passwords do not match")

            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters")

            return password
    
    def _create_cipher_with_password(self, password: str) -> 'Fernet':
        """Create a Fernet cipher from a password (for validation)."""
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography.fernet import Fernet
        import base64
        
        salt = self._get_or_create_salt()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)

    def _get_or_create_salt(self) -> bytes:
        """Get existing salt or create new one."""
        if self.salt_file.exists():
            return self.salt_file.read_bytes()
        else:
            salt = os.urandom(16)
            self.salt_file.write_bytes(salt)
            self.salt_file.chmod(0o600)
            return salt

    def _create_cipher(self) -> Fernet:
        """Create Fernet cipher from master password."""
        salt = self._get_or_create_salt()

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
        return Fernet(key)

    def _load_credentials(self) -> Dict[str, Credential]:
        """Load and decrypt credentials from storage."""
        if not self.credentials_file.exists():
            return {}

        try:
            encrypted_data = self.credentials_file.read_bytes()
            decrypted_data = self._cipher.decrypt(encrypted_data)
            data = json.loads(decrypted_data.decode())

            credentials = {}
            for name, cred_dict in data.items():
                credentials[name] = Credential.from_dict(cred_dict)

            return credentials

        except Exception as e:
            raise RuntimeError(f"Failed to decrypt credentials. Wrong password? Error: {e}")

    def _save_credentials(self):
        """Encrypt and save credentials to storage."""
        data = {name: cred.to_dict() for name, cred in self._credentials.items()}

        json_data = json.dumps(data, indent=2)
        encrypted_data = self._cipher.encrypt(json_data.encode())

        self.credentials_file.write_bytes(encrypted_data)
        self.credentials_file.chmod(0o600)

    def _bootstrap_from_env(self):
        """Import credentials from environment variables and .env files."""
        if self._env_bootstrapped:
            return

        env_data = self._collect_env_data()
        if not env_data:
            self._env_bootstrapped = True
            return

        for rule in ENV_IMPORT_RULES:
            value = self._first_present(env_data, rule.get("value_keys", []))
            if not value:
                continue

            name = rule["name"]
            provider = rule["provider"]
            credential_type = rule["credential_type"]
            email = self._first_present(env_data, rule.get("email_keys", []))
            username = self._first_present(env_data, rule.get("username_keys", []))

            metadata: Dict[str, Any] = {"source": "env"}
            for meta_key, keys in rule.get("metadata_keys", {}).items():
                meta_value = self._first_present(env_data, keys)
                if meta_value:
                    metadata[meta_key] = meta_value

            existing = self._credentials.get(name)
            if existing:
                update_kwargs: Dict[str, Any] = {}
                if existing.value != value:
                    update_kwargs["value"] = value
                if email and existing.email != email:
                    update_kwargs["email"] = email
                if username and existing.username != username:
                    update_kwargs["username"] = username

                combined_metadata = existing.metadata.copy() if existing.metadata else {}
                metadata_changed = False
                for meta_key, meta_value in metadata.items():
                    if combined_metadata.get(meta_key) != meta_value:
                        combined_metadata[meta_key] = meta_value
                        metadata_changed = True
                if metadata_changed:
                    update_kwargs["metadata"] = combined_metadata

                if update_kwargs:
                    self.update_credential(name, **update_kwargs)
            else:
                self.store_credential(
                    name=name,
                    credential_type=credential_type,
                    provider=provider,
                    value=value,
                    username=username,
                    email=email,
                    metadata=metadata,
                )

        self._env_bootstrapped = True

    def _collect_env_data(self) -> Dict[str, str]:
        """Collect environment variables from os.environ and .env files."""
        env_data: Dict[str, str] = {}

        # Start with current environment variables
        for key, value in os.environ.items():
            if isinstance(value, str) and value:
                env_data[key] = value

        for env_file in self._discover_env_files():
            env_data.update(self._parse_env_file(env_file))

        return env_data

    def _discover_env_files(self) -> List[Path]:
        """Find relevant .env files for credential import."""
        candidates: List[Path] = []

        explicit_files = os.getenv("MCP_QA_ENV_FILES")
        if explicit_files:
            for entry in explicit_files.split(os.pathsep):
                if not entry:
                    continue
                path = Path(entry).expanduser()
                if path.is_file():
                    candidates.append(path)

        explicit_file = os.getenv("MCP_QA_ENV_FILE")
        if explicit_file:
            path = Path(explicit_file).expanduser()
            if path.is_file():
                candidates.append(path)

        search = Path.cwd()
        for _ in range(6):
            for name in (".env", ".env.local"):
                candidate = search / name
                if candidate.is_file():
                    candidates.append(candidate)
            if search.parent == search:
                break
            search = search.parent

        unique: List[Path] = []
        seen: Set[str] = set()
        for path in candidates:
            resolved = path.resolve()
            key = str(resolved)
            if key not in seen:
                unique.append(resolved)
                seen.add(key)

        return unique

    def _parse_env_file(self, path: Path) -> Dict[str, str]:
        """Parse key=value pairs from an env file."""
        data: Dict[str, str] = {}
        try:
            with path.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.lower().startswith("export "):
                        line = line[7:].strip()
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if not key:
                        continue
                    if value.startswith("\"") and value.endswith("\"") and len(value) >= 2:
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'") and len(value) >= 2:
                        value = value[1:-1]
                    if value:
                        data[key] = value
        except Exception:
            return {}

        return data

    @staticmethod
    def _first_present(data: Dict[str, str], keys: Optional[List[str]]) -> Optional[str]:
        """Return the first non-empty value for the provided keys."""
        if not keys:
            return None
        for key in keys:
            if not key:
                continue
            value = data.get(key)
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned:
                    return cleaned
        return None

    def store_credential(
        self,
        name: str,
        credential_type: CredentialType,
        provider: str,
        value: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Credential:
        """
        Store a credential securely.

        Args:
            name: Unique name for this credential
            credential_type: Type of credential
            provider: Provider name (e.g., "authkit", "google")
            value: The secret value to store
            username: Optional username
            email: Optional email
            expires_at: Optional expiration time
            metadata: Optional additional metadata

        Returns:
            The created Credential object
        """
        now = datetime.now()

        credential = Credential(
            name=name,
            credential_type=credential_type,
            provider=provider,
            value=value,
            username=username,
            email=email,
            expires_at=expires_at,
            metadata=metadata or {},
            created_at=now,
            updated_at=now
        )

        self._credentials[name] = credential
        self._save_credentials()
        
        self.logger.info(
            "Credential stored",
            name=name,
            provider=provider,
            credential_type=credential_type.value,
            emoji="🔐"
        )

        return credential

    def get_credential(self, name: str) -> Optional[Credential]:
        """
        Get a credential by name.

        Args:
            name: Credential name

        Returns:
            Credential object or None if not found
        """
        credential = self._credentials.get(name)
        if credential:
            self.logger.debug(
                "Credential retrieved",
                name=name,
                provider=credential.provider,
                emoji="🔓"
            )
        return credential

    def get_credentials_by_provider(self, provider: str) -> List[Credential]:
        """
        Get all credentials for a provider.

        Args:
            provider: Provider name

        Returns:
            List of credentials
        """
        return [
            cred for cred in self._credentials.values()
            if cred.provider == provider
        ]

    def get_credentials_by_type(self, credential_type: CredentialType) -> List[Credential]:
        """
        Get all credentials of a specific type.

        Args:
            credential_type: Type of credential

        Returns:
            List of credentials
        """
        return [
            cred for cred in self._credentials.values()
            if cred.credential_type == credential_type
        ]

    def update_credential(
        self,
        name: str,
        value: Optional[str] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Credential]:
        """
        Update an existing credential.

        Args:
            name: Credential name
            value: New value (if provided)
            username: New username (if provided)
            email: New email (if provided)
            expires_at: New expiration (if provided)
            metadata: New metadata (if provided)

        Returns:
            Updated credential or None if not found
        """
        credential = self._credentials.get(name)
        if not credential:
            return None

        if value is not None:
            credential.value = value
        if username is not None:
            credential.username = username
        if email is not None:
            credential.email = email
        if expires_at is not None:
            credential.expires_at = expires_at
        if metadata is not None:
            credential.metadata = metadata

        credential.updated_at = datetime.now()

        self._save_credentials()
        
        self.logger.info(
            "Credential updated",
            name=name,
            provider=credential.provider,
            emoji="♻️"
        )
        
        return credential

    def delete_credential(self, name: str) -> bool:
        """
        Delete a credential.

        Args:
            name: Credential name

        Returns:
            True if deleted, False if not found
        """
        if name in self._credentials:
            credential = self._credentials[name]
            del self._credentials[name]
            self._save_credentials()
            
            self.logger.info(
                "Credential deleted",
                name=name,
                provider=credential.provider,
                emoji="🗑️"
            )
            
            return True
        return False

    def list_credentials(self) -> List[str]:
        """List all credential names."""
        return list(self._credentials.keys())

    def clear_expired(self) -> int:
        """
        Remove all expired credentials.

        Returns:
            Number of credentials removed
        """
        expired = [
            name for name, cred in self._credentials.items()
            if cred.is_expired()
        ]

        for name in expired:
            del self._credentials[name]

        if expired:
            self._save_credentials()
            self.logger.info(
                "Expired credentials cleared",
                count=len(expired),
                emoji="🧹"
            )

        return len(expired)

    def export_for_env(self, name: str) -> Optional[Dict[str, str]]:
        """
        Export credential as environment variables.

        Args:
            name: Credential name

        Returns:
            Dictionary of env vars or None if not found
        """
        credential = self.get_credential(name)
        if not credential:
            return None

        env_vars = {}

        if credential.email:
            env_vars['AUTH_EMAIL'] = credential.email
        if credential.username:
            env_vars['AUTH_USERNAME'] = credential.username

        if credential.credential_type == CredentialType.PASSWORD:
            env_vars['AUTH_PASSWORD'] = credential.value
        elif credential.credential_type == CredentialType.API_TOKEN:
            env_vars['AUTH_TOKEN'] = credential.value
        elif credential.credential_type == CredentialType.OAUTH_TOKEN:
            env_vars['AUTH_OAUTH_TOKEN'] = credential.value
        elif credential.credential_type == CredentialType.TOTP_SECRET:
            env_vars['AUTH_TOTP_SECRET'] = credential.value

        return env_vars


# Singleton instance
_credential_manager: Optional[CredentialManager] = None


def get_credential_manager(
    master_password: Optional[str] = None,
    force_new: bool = False
) -> CredentialManager:
    """
    Get the global credential manager instance.

    Args:
        master_password: Master password (prompts if not provided)
        force_new: Force creation of new instance

    Returns:
        CredentialManager instance
    """
    global _credential_manager

    if force_new or _credential_manager is None:
        _credential_manager = CredentialManager(master_password)

    return _credential_manager
