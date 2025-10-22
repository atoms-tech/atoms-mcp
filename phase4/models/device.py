"""Device information model for session tracking."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any

from user_agents import parse


class DeviceType(Enum):
    """Device type enumeration."""
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    BOT = "bot"
    UNKNOWN = "unknown"


@dataclass
class DeviceInfo:
    """Device/browser information for session tracking.

    Attributes:
        user_agent: Raw user agent string
        device_type: Type of device
        browser: Browser name and version
        os: Operating system name and version
        device_id: Optional persistent device identifier
        device_family: Device family (e.g., iPhone, Galaxy)
        is_bot: Whether this is a bot/crawler
    """

    user_agent: str
    device_type: DeviceType = DeviceType.UNKNOWN
    browser: str = "Unknown"
    os: str = "Unknown"
    device_id: str | None = None
    device_family: str | None = None
    is_bot: bool = False

    @classmethod
    def from_user_agent(
        cls,
        user_agent: str,
        device_id: str | None = None
    ) -> DeviceInfo:
        """Parse device info from user agent string.

        Args:
            user_agent: User agent string
            device_id: Optional device identifier

        Returns:
            DeviceInfo instance
        """
        if not user_agent:
            return cls(
                user_agent="",
                device_type=DeviceType.UNKNOWN,
                device_id=device_id
            )

        try:
            # Parse user agent
            ua = parse(user_agent)

            # Determine device type
            if ua.is_mobile:
                device_type = DeviceType.MOBILE
            elif ua.is_tablet:
                device_type = DeviceType.TABLET
            elif ua.is_pc:
                device_type = DeviceType.DESKTOP
            elif ua.is_bot:
                device_type = DeviceType.BOT
            else:
                device_type = DeviceType.UNKNOWN

            # Extract browser info
            browser = f"{ua.browser.family}"
            if ua.browser.version_string:
                browser += f" {ua.browser.version_string}"

            # Extract OS info
            os = f"{ua.os.family}"
            if ua.os.version_string:
                os += f" {ua.os.version_string}"

            # Extract device family
            device_family = ua.device.family if ua.device.family != "Other" else None

            return cls(
                user_agent=user_agent,
                device_type=device_type,
                browser=browser,
                os=os,
                device_id=device_id,
                device_family=device_family,
                is_bot=ua.is_bot
            )

        except Exception:
            # Fallback if parsing fails
            return cls(
                user_agent=user_agent,
                device_type=DeviceType.UNKNOWN,
                device_id=device_id
            )

    def generate_fingerprint(self) -> str:
        """Generate a device fingerprint for tracking.

        Returns:
            SHA256 hash of device characteristics
        """
        # Combine device characteristics
        fingerprint_data = f"{self.user_agent}:{self.device_type.value}:{self.browser}:{self.os}"

        if self.device_id:
            fingerprint_data += f":{self.device_id}"

        # Generate hash
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]

    def is_suspicious_change(self, other: DeviceInfo) -> bool:
        """Check if device change is suspicious.

        Args:
            other: Device info to compare

        Returns:
            True if change is suspicious
        """
        if not other:
            return False

        # Same device ID means trusted
        if self.device_id and self.device_id == other.device_id:
            return False

        # Check for major changes
        suspicious_changes = [
            # OS family change (e.g., Windows to Mac)
            self.os.split()[0] != other.os.split()[0],
            # Device type change (e.g., mobile to desktop)
            self.device_type != other.device_type and
            self.device_type != DeviceType.UNKNOWN and
            other.device_type != DeviceType.UNKNOWN,
            # Bot detection
            not self.is_bot and other.is_bot,
        ]

        return any(suspicious_changes)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "user_agent": self.user_agent,
            "device_type": self.device_type.value,
            "browser": self.browser,
            "os": self.os,
            "device_id": self.device_id,
            "device_family": self.device_family,
            "is_bot": self.is_bot,
            "fingerprint": self.generate_fingerprint(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceInfo:
        """Create from dictionary.

        Args:
            data: Dictionary data

        Returns:
            DeviceInfo instance
        """
        # Convert device_type string to enum
        if "device_type" in data and isinstance(data["device_type"], str):
            data["device_type"] = DeviceType(data["device_type"])

        # Remove non-model fields
        data.pop("fingerprint", None)

        return cls(**data)
