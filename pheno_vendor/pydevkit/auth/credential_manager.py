"""
Interactive credential management for OAuth flows.

Provides utilities for prompting and securely storing OAuth credentials.
"""

from typing import Optional, Dict, Any, Callable
import os
import json
import getpass
from pathlib import Path


class InteractiveCredentialManager:
    """
    Manage OAuth credentials with interactive prompts.

    Handles secure storage and retrieval of OAuth credentials
    with interactive fallback for missing values.

    Example:
        manager = InteractiveCredentialManager("my_app")

        # Get credentials (prompts if not found)
        creds = manager.get_credentials(
            required_fields=["client_id", "client_secret"]
        )

        # Save for next time
        manager.save_credentials(creds)
    """

    def __init__(
        self,
        app_name: str,
        config_dir: Optional[Path] = None,
        auto_save: bool = True,
    ):
        """
        Initialize credential manager.

        Args:
            app_name: Application name for config file
            config_dir: Custom config directory (defaults to ~/.config)
            auto_save: Automatically save credentials after prompting
        """
        self.app_name = app_name
        self.auto_save = auto_save

        if config_dir is None:
            config_dir = Path.home() / ".config" / app_name
        self.config_dir = config_dir
        self.config_file = config_dir / "credentials.json"

    def get_credentials(
        self,
        required_fields: Optional[list[str]] = None,
        optional_fields: Optional[list[str]] = None,
        prompts: Optional[Dict[str, str]] = None,
        secure_fields: Optional[set[str]] = None,
    ) -> Dict[str, str]:
        """
        Get credentials, prompting for missing values.

        Args:
            required_fields: Required credential fields
            optional_fields: Optional credential fields
            prompts: Custom prompts for each field
            secure_fields: Fields to prompt for securely (hidden input)

        Returns:
            Dictionary of credentials

        Example:
            creds = manager.get_credentials(
                required_fields=["client_id", "client_secret"],
                secure_fields={"client_secret"}
            )
        """
        required_fields = required_fields or []
        optional_fields = optional_fields or []
        prompts = prompts or {}
        secure_fields = secure_fields or {"client_secret", "api_key", "password"}

        # Load existing credentials
        existing = self.load_credentials()

        # Collect all credentials
        credentials = {}

        # Required fields
        for field in required_fields:
            if field in existing:
                credentials[field] = existing[field]
            else:
                prompt = prompts.get(field, f"Enter {field}")
                if field in secure_fields:
                    value = getpass.getpass(f"{prompt}: ")
                else:
                    value = input(f"{prompt}: ")
                credentials[field] = value

        # Optional fields
        for field in optional_fields:
            if field in existing:
                credentials[field] = existing[field]
            else:
                prompt = prompts.get(field, f"Enter {field} (optional)")
                try:
                    if field in secure_fields:
                        value = getpass.getpass(f"{prompt}: ")
                    else:
                        value = input(f"{prompt}: ")
                    if value:
                        credentials[field] = value
                except KeyboardInterrupt:
                    continue

        # Auto-save if enabled and we prompted for anything
        if self.auto_save and credentials != existing:
            self.save_credentials(credentials)

        return credentials

    def load_credentials(self) -> Dict[str, str]:
        """
        Load credentials from storage.

        Returns:
            Dictionary of stored credentials
        """
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def save_credentials(self, credentials: Dict[str, str]) -> None:
        """
        Save credentials to storage.

        Args:
            credentials: Credentials to save
        """
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Save with restrictive permissions
        with open(self.config_file, 'w') as f:
            json.dump(credentials, f, indent=2)

        # Set file permissions to user-only (Unix-like systems)
        try:
            os.chmod(self.config_file, 0o600)
        except (OSError, AttributeError):
            # Windows doesn't support chmod
            pass

    def clear_credentials(self) -> None:
        """Remove saved credentials."""
        if self.config_file.exists():
            self.config_file.unlink()

    def has_credentials(self, required_fields: Optional[list[str]] = None) -> bool:
        """
        Check if all required credentials are available.

        Args:
            required_fields: Fields to check for

        Returns:
            True if all required fields are present
        """
        if not required_fields:
            return self.config_file.exists()

        existing = self.load_credentials()
        return all(field in existing for field in required_fields)


def ensure_oauth_credentials(
    app_name: str,
    required_fields: Optional[list[str]] = None,
    config_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """
    Ensure OAuth credentials exist, prompting if necessary.

    Convenience function for one-time credential setup.

    Args:
        app_name: Application name
        required_fields: Required credential fields
        config_dir: Custom config directory

    Returns:
        Dictionary of credentials

    Example:
        creds = ensure_oauth_credentials(
            "my_app",
            required_fields=["client_id", "client_secret"]
        )
    """
    manager = InteractiveCredentialManager(app_name, config_dir=config_dir)
    return manager.get_credentials(required_fields=required_fields)


def prompt_for_value(
    field_name: str,
    prompt: Optional[str] = None,
    secure: bool = False,
    default: Optional[str] = None,
    validator: Optional[Callable[[str], bool]] = None,
) -> str:
    """
    Prompt user for a single value with validation.

    Args:
        field_name: Name of the field
        prompt: Custom prompt text
        secure: Use secure input (hidden)
        default: Default value
        validator: Optional validation function

    Returns:
        User-provided value

    Example:
        email = prompt_for_value(
            "email",
            validator=lambda x: "@" in x
        )
    """
    prompt_text = prompt or f"Enter {field_name}"
    if default:
        prompt_text += f" [{default}]"
    prompt_text += ": "

    while True:
        if secure:
            value = getpass.getpass(prompt_text)
        else:
            value = input(prompt_text)

        # Use default if provided and input is empty
        if not value and default:
            value = default

        # Validate
        if validator and not validator(value):
            print(f"Invalid {field_name}, please try again.")
            continue

        return value


__all__ = [
    "InteractiveCredentialManager",
    "ensure_oauth_credentials",
    "prompt_for_value",
]
