"""Test schemas triggers for comprehensive coverage."""

from datetime import UTC, datetime
from unittest.mock import patch

from schemas.constants import Fields
from schemas.triggers import (
    auto_generate_slug,
    generate_external_id,
    handle_updated_at,
    normalize_slug,
    set_created_timestamps,
)


class TestSlugNormalization:
    """Test slug normalization functions."""

    def test_normalize_slug_basic(self):
        """Test basic slug normalization."""
        assert normalize_slug("Test Project") == "test-project"
        assert normalize_slug("User Dashboard") == "user-dashboard"
        assert normalize_slug("API Documentation") == "api-documentation"

    def test_normalize_slug_spaces(self):
        """Test slug normalization with multiple spaces."""
        assert normalize_slug("Project   With   Spaces") == "project-with-spaces"
        assert normalize_slug("Multiple     Spaces") == "multiple-spaces"
        assert normalize_slug("   Leading Spaces") == "leading-spaces"
        assert normalize_slug("Trailing Spaces   ") == "trailing-spaces"

    def test_normalize_slug_special_chars(self):
        """Test slug normalization with special characters."""
        assert normalize_slug("Special_Chars!@#$") == "special-chars"
        assert normalize_slug("Test&Project") == "test-project"
        assert normalize_slug("Project/Document") == "project-document"
        assert normalize_slug("Test.Project.Name") == "test-project-name"

    def test_normalize_slug_dashes(self):
        """Test slug normalization with dashes."""
        assert normalize_slug("Multiple---Dashes") == "multiple-dashes"
        assert normalize_slug("Leading--Dash") == "leading-dash"
        assert normalize_slug("Trailing-Dash-") == "trailing-dash"
        assert normalize_slug("----Many-Dashes----") == "many-dashes"

    def test_normalize_slug_edge_cases(self):
        """Test slug normalization edge cases."""
        assert normalize_slug("") == ""
        assert normalize_slug("   ") == ""
        assert normalize_slug("---") == "-"
        assert normalize_slug("___") == "_"
        assert normalize_slug("123") == "123"
        assert normalize_slug("A") == "a"
        assert normalize_slug("a") == "a"
        assert normalize_slug("123ABC") == "123abc"

    def test_normalize_slug_unicode(self):
        """Test slug normalization with unicode characters."""
        assert normalize_slug("Tëst Prøjëct") == "t-st-pr-j-ct"
        assert normalize_slug("Ünicöde Tëst") == "-nic-de-t-st"
        assert normalize_slug("Café Restaurant") == "caf-restaurant"


class TestAutoGenerateSlug:
    """Test automatic slug generation."""

    def test_auto_generate_slug_from_name(self):
        """Test slug generation from name."""
        assert auto_generate_slug("Test Project") == "test-project"
        assert auto_generate_slug("User Dashboard") == "user-dashboard"
        assert auto_generate_slug("API Documentation") == "api-documentation"

    def test_auto_generate_slug_with_existing_slug(self):
        """Test slug generation with existing slug."""
        assert auto_generate_slug("Test", slug="existing-slug") == "existing-slug"
        assert auto_generate_slug("Test", slug="custom-slug-123") == "custom-slug-123"
        assert auto_generate_slug("Project", slug="proj-abc-def") == "proj-abc-def"

    def test_auto_generate_slug_with_metadata(self):
        """Test slug generation with metadata."""
        metadata = {"type": "project", "category": "web"}

        # Should generate slug from name when no slug provided
        result = auto_generate_slug("Web Project", metadata=metadata)
        assert result == "web-project"

        # Should use existing slug when provided
        result = auto_generate_slug("Web Project", slug="custom-slug", metadata=metadata)
        assert result == "custom-slug"

    def test_auto_generate_slug_edge_cases(self):
        """Test slug generation edge cases."""
        # Empty name should still work with slug
        result = auto_generate_slug("", slug="manual-slug")
        assert result == "manual-slug"

        # Special characters in name
        result = auto_generate_slug("Project@#$%", slug="clean-slug")
        assert result == "clean-slug"


class TestTimestampHandling:
    """Test timestamp handling functions."""

    def test_handle_updated_at_basic(self):
        """Test basic updated_at handling."""
        data = {"name": "test"}
        result = handle_updated_at(data)

        assert "updated_at" in result
        assert isinstance(result["updated_at"], datetime)
        assert result["updated_at"].tzinfo is not None

        # Original data should be preserved
        assert result["name"] == "test"

    def test_handle_updated_at_existing_timestamp(self):
        """Test updated_at with existing timestamp."""
        existing_time = datetime.now(UTC)
        data = {"name": "test", "updated_at": existing_time}

        result = handle_updated_at(data)

        assert "updated_at" in result
        # Should update timestamp
        assert result["updated_at"] >= existing_time

        # Original data should be preserved
        assert result["name"] == "test"

    def test_handle_updated_at_without_update(self):
        """Test updated_at when no update needed."""
        existing_time = datetime.now(UTC)
        data = {"name": "test", "updated_at": existing_time}

        result = handle_updated_at(data, update_timestamp=False)

        assert "updated_at" in result
        # Should preserve timestamp
        assert result["updated_at"] == existing_time

    def test_set_created_timestamps_new_record(self):
        """Test setting timestamps for new records."""
        data = {"name": "test"}

        result = set_created_timestamps(data)

        assert "created_at" in result
        assert "updated_at" in result
        assert isinstance(result["created_at"], datetime)
        assert isinstance(result["updated_at"], datetime)
        assert result["created_at"].tzinfo is not None
        assert result["updated_at"].tzinfo is not None
        assert result["created_at"] == result["updated_at"]  # Should be same for new records

        # Original data should be preserved
        assert result["name"] == "test"

    def test_set_created_timestamps_existing_record(self):
        """Test setting timestamps for existing records."""
        existing_time = datetime.now(UTC)
        data = {"name": "test", "created_at": existing_time}

        result = set_created_timestamps(data)

        assert "created_at" in result
        assert "updated_at" in result
        # Should update both timestamps
        assert result["updated_at"] >= existing_time

        # Original data should be preserved
        assert result["name"] == "test"

    def test_set_created_timestamps_with_both_existing(self):
        """Test setting timestamps when both exist."""
        created_time = datetime.now(UTC)
        updated_time = datetime.now(UTC)
        data = {
            "name": "test",
            "created_at": created_time,
            "updated_at": updated_time
        }

        result = set_created_timestamps(data)

        assert "created_at" in result
        assert "updated_at" in result
        # Should update both timestamps
        assert result["updated_at"] >= updated_time


class TestExternalIdGeneration:
    """Test external ID generation."""

    def test_generate_external_id_basic(self):
        """Test basic external ID generation."""
        external_id = generate_external_id("project")

        assert isinstance(external_id, str)
        assert len(external_id) > 0
        assert "proj_" in external_id  # Should contain entity type prefix

    def test_generate_external_id_different_entities(self):
        """Test external ID generation for different entities."""
        project_id = generate_external_id("project")
        document_id = generate_external_id("document")
        user_id = generate_external_id("user")
        org_id = generate_external_id("organization")

        # All IDs should be strings
        for id_value in [project_id, document_id, user_id, org_id]:
            assert isinstance(id_value, str)
            assert len(id_value) > 0

        # IDs should contain entity prefixes
        assert "proj_" in project_id
        assert "doc_" in document_id
        assert "user_" in user_id
        assert "org_" in org_id

        # IDs should be different
        assert project_id != document_id
        assert document_id != user_id
        assert user_id != org_id
        assert org_id != project_id

    @patch("schemas.triggers.uuid.uuid4")
    def test_generate_external_id_deterministic(self, mock_uuid):
        """Test external ID generation with mocked UUID."""
        mock_uuid.return_value.hex = "123456789abcdef"

        project_id = generate_external_id("project")
        document_id = generate_external_id("document")

        # Should contain the mocked UUID
        assert "123456789abcdef" in project_id
        assert "123456789abcdef" in document_id

        # Should be different due to entity type
        assert project_id != document_id

    def test_generate_external_id_invalid_entity(self):
        """Test external ID generation with invalid entity."""
        # Should still work but may not have proper prefix
        id_value = generate_external_id("invalid_entity")

        assert isinstance(id_value, str)
        assert len(id_value) > 0


class TestTriggerIntegration:
    """Test trigger function integration scenarios."""

    def test_complete_record_creation(self):
        """Test complete record creation workflow."""
        # Start with basic data
        data = {
            "name": "Test Project",
            "description": "A test project"
        }

        # Apply all trigger functions in order
        data["slug"] = auto_generate_slug(data["name"])
        data = set_created_timestamps(data)
        data[Fields.EXTERNAL_ID] = generate_external_id("project")

        # Verify complete record
        assert "slug" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert Fields.EXTERNAL_ID in data
        assert data["slug"] == "test-project"
        assert isinstance(data["created_at"], datetime)
        assert isinstance(data["updated_at"], datetime)
        assert isinstance(data[Fields.EXTERNAL_ID], str)

    def test_complete_record_update(self):
        """Test complete record update workflow."""
        # Start with existing data
        created_time = datetime.now(UTC)
        data = {
            "id": "proj-123",
            "name": "Updated Project",
            "description": "Updated description",
            "created_at": created_time,
            "updated_at": created_time
        }

        # Apply update triggers
        data = handle_updated_at(data)
        if "name" in data:
            data["slug"] = auto_generate_slug(data["name"], slug=data.get("slug"))

        # Verify updated record
        assert "updated_at" in data
        assert data["updated_at"] >= created_time
        assert data["name"] == "Updated Project"

    def test_trigger_error_handling(self):
        """Test trigger function error handling."""
        # Test with None data
        try:
            result = handle_updated_at(None)
            assert isinstance(result, dict)
        except (TypeError, AttributeError):
            # Acceptable to raise type errors
            pass

        # Test with empty data
        result = handle_updated_at({})
        assert isinstance(result, dict)
        assert "updated_at" in result

        # Test slug generation with None
        try:
            slug = auto_generate_slug(None, slug="fallback-slug")
            assert slug == "fallback-slug"
        except (TypeError, AttributeError):
            # Acceptable to raise type errors
            pass

    def test_timestamp_consistency(self):
        """Test timestamp consistency across functions."""
        data = {"name": "test"}

        # Create timestamps
        result1 = set_created_timestamps(data.copy())

        # Wait a tiny bit to ensure different timestamps
        import time
        time.sleep(0.001)

        # Update timestamps
        result2 = handle_updated_at(result1.copy())

        # Verify consistency
        assert result1["created_at"] == result1["updated_at"]
        assert result2["updated_at"] >= result1["updated_at"]
        assert result1["created_at"] < result2["updated_at"]

    def test_slug_uniqueness(self):
        """Test slug uniqueness in different contexts."""
        base_name = "Test Project"

        # Generate slugs in different ways
        slug1 = auto_generate_slug(base_name)
        slug2 = auto_generate_slug(base_name)
        slug3 = normalize_slug(base_name)

        # Auto-generated should be deterministic
        assert slug1 == slug2
        assert slug1 == slug3

        # Manual slug should override
        slug_manual = auto_generate_slug(base_name, slug="custom-slug")
        assert slug_manual == "custom-slug"
        assert slug_manual != slug1

    def test_external_id_format(self):
        """Test external ID format consistency."""
        entities = ["project", "document", "user", "organization"]
        ids = []

        for entity in entities:
            id_value = generate_external_id(entity)
            ids.append(id_value)

            # Check format: prefix_uuid
            parts = id_value.split("_", 1)
            assert len(parts) == 2
            assert parts[0] in ["proj", "doc", "user", "org"]
            assert len(parts[1]) == 32  # UUID hex length
            assert parts[1].isalnum()  # Should be alphanumeric

        # All IDs should be unique
        assert len(set(ids)) == len(ids)


# Edge case tests for maximum coverage
class TestTriggerEdgeCases:
    """Test trigger function edge cases."""

    def test_normalize_slug_extreme_cases(self):
        """Test slug normalization extreme cases."""
        # Very long string
        long_string = "A" * 1000
        result = normalize_slug(long_string)
        assert len(result) <= 1000
        assert all(c.islower() or c.isdigit() or c in "-_" for c in result)

        # Mixed case and special chars
        mixed = "123ABCdef!@#$%^&*()_+-={}[]|\\:;\"'<>,.?/"
        result = normalize_slug(mixed)
        assert isinstance(result, str)
        assert len(result) > 0

        # Only special chars
        special = "!@#$%^&*()_+-={}[]|\\:;\"'<>,.?/"
        result = normalize_slug(special)
        assert isinstance(result, str)

    def test_timestamp_edge_cases(self):
        """Test timestamp handling edge cases."""
        # Test with timezone-aware timestamps
        aware_time = datetime.now(UTC)
        data = {"name": "test", "updated_at": aware_time}
        result = handle_updated_at(data)

        assert isinstance(result["updated_at"], datetime)
        assert result["updated_at"].tzinfo is not None

        # Test with timezone-naive timestamps
        naive_time = datetime.now()
        data = {"name": "test", "updated_at": naive_time}
        result = handle_updated_at(data)

        assert isinstance(result["updated_at"], datetime)

    def test_external_id_edge_cases(self):
        """Test external ID generation edge cases."""
        # Test with uppercase entity
        upper_id = generate_external_id("PROJECT")
        assert isinstance(upper_id, str)
        assert len(upper_id) > 0

        # Test with numeric entity
        numeric_id = generate_external_id("123")
        assert isinstance(numeric_id, str)
        assert len(numeric_id) > 0

        # Test with special characters in entity
        special_id = generate_external_id("project-v2")
        assert isinstance(special_id, str)
        assert len(special_id) > 0

    def test_trigger_performance_considerations(self):
        """Test trigger functions with performance considerations."""

        # Test with large dataset
        large_data = []
        for i in range(100):
            data = {
                "name": f"Test Project {i}",
                "description": f"Description for project {i}"
            }
            data["slug"] = auto_generate_slug(data["name"])
            data = set_created_timestamps(data)
            data[Fields.EXTERNAL_ID] = generate_external_id("project")
            large_data.append(data)

        # Verify all records were processed
        assert len(large_data) == 100

        # Verify each record has required fields
        for data in large_data:
            assert "slug" in data
            assert "created_at" in data
            assert "updated_at" in data
            assert Fields.EXTERNAL_ID in data
            assert data["slug"].startswith("test-project-")

    def test_trigger_thread_safety(self):
        """Test trigger function thread safety considerations."""
        import threading
        import time

        results = []
        errors = []

        def generate_ids():
            try:
                for _ in range(10):
                    id_value = generate_external_id("project")
                    results.append(id_value)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Run in multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=generate_ids)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0

        # Verify all IDs were generated
        assert len(results) == 50

        # Verify all IDs are unique (very high probability)
        assert len(set(results)) == 50
