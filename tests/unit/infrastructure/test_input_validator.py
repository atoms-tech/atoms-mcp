"""Tests for input validation and sanitization."""

import pytest
from infrastructure.input_validator import InputValidator, validate_entity_data


class TestStringValidation:
    """Test string field validation."""

    def test_valid_string(self):
        """Test valid string passes validation."""
        result = InputValidator.validate_string("Hello World", "test")
        assert result == "Hello World"

    def test_empty_string_allowed(self):
        """Test empty string allowed when specified."""
        result = InputValidator.validate_string("", "test", allow_empty=True)
        assert result == ""

    def test_empty_string_disallowed(self):
        """Test empty string rejected by default."""
        with pytest.raises(ValueError):
            InputValidator.validate_string("", "test", allow_empty=False)

    def test_whitespace_trimmed(self):
        """Test leading/trailing whitespace trimmed."""
        result = InputValidator.validate_string("  hello  ", "test")
        assert result == "hello"

    def test_none_value_rejected(self):
        """Test None value rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string(None, "test")

    def test_non_string_type_rejected(self):
        """Test non-string types rejected."""
        with pytest.raises(TypeError):
            InputValidator.validate_string(123, "test")

    def test_max_length_enforced(self):
        """Test maximum length enforced."""
        long_string = "x" * 2000
        with pytest.raises(ValueError):
            InputValidator.validate_string(long_string, "test", max_length=1000)

    def test_max_length_default(self):
        """Test default max length used."""
        long_string = "x" * 2000
        with pytest.raises(ValueError):
            InputValidator.validate_string(long_string, "test")

    # SQL Injection tests
    def test_sql_injection_single_quote(self):
        """Test SQL injection with single quote rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string("'; DROP TABLE users; --", "test")

    def test_sql_injection_double_quote(self):
        """Test SQL injection with double quote rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string('" OR "1"="1', "test")

    def test_sql_injection_comment(self):
        """Test SQL injection with comment rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string("admin' --", "test")

    def test_sql_injection_union(self):
        """Test SQL injection with UNION rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string("1 UNION SELECT * FROM users", "test")

    def test_sql_injection_drop(self):
        """Test SQL injection with DROP rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string("value'; DROP TABLE entities; --", "test")

    # XSS tests
    def test_xss_script_tag(self):
        """Test XSS with script tag rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string("<script>alert('xss')</script>", "test")

    def test_xss_javascript_protocol(self):
        """Test XSS with javascript protocol rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string("javascript:alert('xss')", "test")

    def test_xss_event_handler(self):
        """Test XSS with event handler rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string("<img onerror='alert(1)'>", "test")

    def test_xss_iframe(self):
        """Test XSS with iframe rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string("<iframe src='evil.com'></iframe>", "test")

    def test_xss_object_tag(self):
        """Test XSS with object tag rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string("<object data='evil'></object>", "test")

    def test_html_allowed_when_specified(self):
        """Test HTML allowed when explicitly enabled."""
        html = "<b>Bold</b>"
        result = InputValidator.validate_string(html, "test", allow_html=True)
        assert result == html

    def test_null_byte_rejected(self):
        """Test null bytes rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_string("test\x00string", "test")

    def test_special_characters_allowed(self):
        """Test allowed special characters work."""
        valid_inputs = [
            "John O'Brien",
            "test-name",
            "test_123",
            "Test (Parentheses)",
            "test@example.com",
            "100% complete",
            "C++ programming",
        ]
        for input_str in valid_inputs:
            result = InputValidator.validate_string(input_str, "test")
            assert result == input_str


class TestIdValidation:
    """Test ID field validation."""

    def test_valid_uuid(self):
        """Test valid UUID format."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = InputValidator.validate_id(uuid)
        assert result == uuid

    def test_valid_slug(self):
        """Test valid slug format."""
        slug = "req-123-abc"
        result = InputValidator.validate_id(slug)
        assert result == slug

    def test_invalid_characters(self):
        """Test invalid characters rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_id("req@123")

    def test_whitespace_trimmed(self):
        """Test whitespace trimmed."""
        result = InputValidator.validate_id("  req-123  ")
        assert result == "req-123"

    def test_empty_id_rejected(self):
        """Test empty ID rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_id("")

    def test_id_too_long(self):
        """Test ID too long rejected."""
        long_id = "a" * 200
        with pytest.raises(ValueError):
            InputValidator.validate_id(long_id)


class TestEmailValidation:
    """Test email field validation."""

    def test_valid_email(self):
        """Test valid email passes."""
        result = InputValidator.validate_email("user@example.com")
        assert result == "user@example.com"

    def test_email_lowercase(self):
        """Test email converted to lowercase."""
        result = InputValidator.validate_email("User@Example.COM")
        assert result == "user@example.com"

    def test_invalid_email_no_domain(self):
        """Test email without domain rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_email("user@")

    def test_invalid_email_no_at(self):
        """Test email without @ rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_email("user.example.com")

    def test_email_with_special_chars(self):
        """Test email with allowed special chars."""
        result = InputValidator.validate_email("user+tag@example.co.uk")
        assert result == "user+tag@example.co.uk"


class TestUrlValidation:
    """Test URL field validation."""

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        result = InputValidator.validate_url("http://example.com/path")
        assert result == "http://example.com/path"

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        result = InputValidator.validate_url("https://example.com/path")
        assert result == "https://example.com/path"

    def test_invalid_url_no_protocol(self):
        """Test URL without protocol rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_url("example.com")

    def test_invalid_url_ftp(self):
        """Test FTP URL rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_url("ftp://example.com")


class TestIntegerValidation:
    """Test integer field validation."""

    def test_valid_integer(self):
        """Test valid integer passes."""
        result = InputValidator.validate_integer(42, "test")
        assert result == 42

    def test_string_integer_converted(self):
        """Test string integer converted."""
        result = InputValidator.validate_integer("123", "test")
        assert result == 123

    def test_min_value_enforced(self):
        """Test minimum value enforced."""
        with pytest.raises(ValueError):
            InputValidator.validate_integer(-1, "test", min_val=0)

    def test_max_value_enforced(self):
        """Test maximum value enforced."""
        with pytest.raises(ValueError):
            InputValidator.validate_integer(2000000, "test", max_val=1000000)

    def test_non_integer_rejected(self):
        """Test non-integer rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_integer("not a number", "test")


class TestBooleanValidation:
    """Test boolean field validation."""

    def test_true_boolean(self):
        """Test True boolean."""
        assert InputValidator.validate_boolean(True) is True

    def test_false_boolean(self):
        """Test False boolean."""
        assert InputValidator.validate_boolean(False) is False

    def test_true_string_variations(self):
        """Test string variations of true."""
        for value in ["true", "TRUE", "1", "yes", "on"]:
            assert InputValidator.validate_boolean(value) is True

    def test_false_string_variations(self):
        """Test string variations of false."""
        for value in ["false", "FALSE", "0", "no", "off"]:
            assert InputValidator.validate_boolean(value) is False

    def test_integer_1_is_true(self):
        """Test integer 1 is True."""
        assert InputValidator.validate_boolean(1) is True

    def test_integer_0_is_false(self):
        """Test integer 0 is False."""
        assert InputValidator.validate_boolean(0) is False


class TestEnumValidation:
    """Test enum field validation."""

    def test_valid_enum_value(self):
        """Test valid enum value."""
        result = InputValidator.validate_enum(
            "draft", "status", ["draft", "active", "archived"]
        )
        assert result == "draft"

    def test_invalid_enum_value(self):
        """Test invalid enum value rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_enum(
                "invalid", "status", ["draft", "active", "archived"]
            )

    def test_enum_case_sensitive(self):
        """Test enum matching is case-sensitive."""
        with pytest.raises(ValueError):
            InputValidator.validate_enum(
                "Draft", "status", ["draft", "active", "archived"]
            )


class TestDictValidation:
    """Test dictionary field validation."""

    def test_valid_dict(self):
        """Test valid dictionary passes."""
        data = {"key": "value"}
        result = InputValidator.validate_dict(data, "test")
        assert result == data

    def test_required_keys_enforced(self):
        """Test required keys enforced."""
        with pytest.raises(ValueError):
            InputValidator.validate_dict(
                {"a": 1}, "test", required_keys=["a", "b"]
            )

    def test_unknown_keys_rejected(self):
        """Test unknown keys rejected."""
        with pytest.raises(ValueError):
            InputValidator.validate_dict(
                {"a": 1, "b": 2, "c": 3},
                "test",
                allowed_keys=["a", "b"]
            )

    def test_non_dict_rejected(self):
        """Test non-dict rejected."""
        with pytest.raises(TypeError):
            InputValidator.validate_dict(["a", "b"], "test")


class TestListValidation:
    """Test list field validation."""

    def test_valid_list(self):
        """Test valid list passes."""
        data = [1, 2, 3]
        result = InputValidator.validate_list(data, "test")
        assert result == data

    def test_min_items_enforced(self):
        """Test minimum items enforced."""
        with pytest.raises(ValueError):
            InputValidator.validate_list([], "test", min_items=1)

    def test_max_items_enforced(self):
        """Test maximum items enforced."""
        with pytest.raises(ValueError):
            InputValidator.validate_list(
                list(range(2000)), "test", max_items=1000
            )

    def test_non_list_rejected(self):
        """Test non-list rejected."""
        with pytest.raises(TypeError):
            InputValidator.validate_list("not a list", "test")


class TestEntityDataValidation:
    """Test complete entity data validation."""

    def test_validate_entity_with_all_fields(self):
        """Test validating entity with all common fields."""
        data = {
            "name": "Test Entity",
            "title": "Test Title",
            "description": "Test description",
            "status": "draft",
            "priority": "high",
            "email": "test@example.com",
            "external_id": "ext-123",
        }
        result = validate_entity_data("requirement", data)
        assert result["name"] == "Test Entity"
        assert result["status"] == "draft"
        assert result["priority"] == "high"

    def test_entity_validation_rejects_invalid_status(self):
        """Test invalid status rejected in entity validation."""
        with pytest.raises(ValueError):
            validate_entity_data("requirement", {"status": "invalid"})

    def test_entity_validation_sanitizes_special_chars(self):
        """Test special chars are handled in entity validation."""
        data = {"name": "O'Brien"}
        result = validate_entity_data("requirement", data)
        assert result["name"] == "O'Brien"


class TestSecurityEdgeCases:
    """Test edge cases and security scenarios."""

    def test_polyglot_sql_xss_injection(self):
        """Test combined SQL/XSS payload rejected."""
        payload = "'; <script>alert('xss')</script> --"
        with pytest.raises(ValueError):
            InputValidator.validate_string(payload, "test")

    def test_unicode_normalization(self):
        """Test Unicode characters handled safely."""
        result = InputValidator.validate_string("Café", "test")
        assert "Café" in result or "Caf" in result

    def test_very_long_string_performance(self):
        """Test very long strings don't cause DoS."""
        long_string = "x" * 100000
        with pytest.raises(ValueError):
            InputValidator.validate_string(long_string, "test", max_length=1000)

    def test_binary_data_rejected(self):
        """Test binary data rejected."""
        with pytest.raises((ValueError, TypeError)):
            InputValidator.validate_string(b"binary", "test")

    def test_nested_injection_attempt(self):
        """Test nested injection attempt rejected."""
        payload = "test<![CDATA[<script>alert(1)</script>]]>"
        with pytest.raises(ValueError):
            InputValidator.validate_string(payload, "test")
