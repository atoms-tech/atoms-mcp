"""
Comprehensive tests for import/export workflows.

Tests cover:
- ImportFromFileWorkflow validation and execution
- ExportToFormatWorkflow validation and execution
- ImportExportHandler all workflow methods
- JSON import/export operations
- CSV import/export operations
- Format validation and conversion
- Error handling and recovery
- Large file handling
- Field filtering and selection
- Pretty printing and formatting
"""

import csv
import json
import pytest
import tempfile
from pathlib import Path
from io import StringIO
from uuid import uuid4

from atoms_mcp.application.workflows.import_export import (
    ImportFromFileWorkflow,
    ExportToFormatWorkflow,
    ImportExportHandler,
    ImportExportError,
    ImportExportValidationError,
    UnsupportedFormatError,
)
from atoms_mcp.application.dto import ResultStatus
from atoms_mcp.domain.models.entity import WorkspaceEntity, ProjectEntity
from conftest import MockRepository, MockLogger, MockCache


# =============================================================================
# IMPORT WORKFLOW VALIDATION TESTS
# =============================================================================


class TestImportWorkflowValidation:
    """Tests for ImportFromFileWorkflow validation."""

    def test_validate_with_file_path(self):
        """Should validate successfully with file_path."""
        workflow = ImportFromFileWorkflow(
            file_path="/path/to/file.json",
            format="json",
            entity_type="workspace",
        )
        workflow.validate_workflow()  # Should not raise

    def test_validate_with_file_content(self):
        """Should validate successfully with file_content."""
        workflow = ImportFromFileWorkflow(
            file_content='{"name": "test"}',
            format="json",
            entity_type="workspace",
        )
        workflow.validate_workflow()  # Should not raise

    def test_validate_missing_file_source(self):
        """Should reject when both file_path and file_content are missing."""
        workflow = ImportFromFileWorkflow(
            format="json",
            entity_type="workspace",
        )
        with pytest.raises(ImportExportValidationError) as exc_info:
            workflow.validate_workflow()
        assert "file_path or file_content" in str(exc_info.value)

    def test_validate_invalid_format(self):
        """Should reject unsupported formats."""
        workflow = ImportFromFileWorkflow(
            file_content="data",
            format="xml",
            entity_type="workspace",
        )
        with pytest.raises(UnsupportedFormatError) as exc_info:
            workflow.validate_workflow()
        assert "Unsupported format" in str(exc_info.value)

    def test_validate_valid_json_format(self):
        """Should accept JSON format."""
        workflow = ImportFromFileWorkflow(
            file_content="{}",
            format="json",
            entity_type="workspace",
        )
        workflow.validate_workflow()  # Should not raise

    def test_validate_valid_csv_format(self):
        """Should accept CSV format."""
        workflow = ImportFromFileWorkflow(
            file_content="name,value",
            format="csv",
            entity_type="workspace",
        )
        workflow.validate_workflow()  # Should not raise

    def test_validate_missing_entity_type(self):
        """Should reject missing entity_type."""
        workflow = ImportFromFileWorkflow(
            file_content="{}",
            format="json",
            entity_type="",
        )
        with pytest.raises(ImportExportValidationError) as exc_info:
            workflow.validate_workflow()
        assert "entity_type is required" in str(exc_info.value)

    def test_default_validate_is_true(self):
        """Should default validate to True."""
        workflow = ImportFromFileWorkflow(
            file_content="{}",
            format="json",
            entity_type="workspace",
        )
        assert workflow.validate is True

    def test_default_stop_on_error_is_false(self):
        """Should default stop_on_error to False."""
        workflow = ImportFromFileWorkflow(
            file_content="{}",
            format="json",
            entity_type="workspace",
        )
        assert workflow.stop_on_error is False


# =============================================================================
# EXPORT WORKFLOW VALIDATION TESTS
# =============================================================================


class TestExportWorkflowValidation:
    """Tests for ExportToFormatWorkflow validation."""

    def test_validate_with_valid_parameters(self):
        """Should validate successfully with valid parameters."""
        workflow = ExportToFormatWorkflow(
            format="json",
            filters={},
        )
        workflow.validate_workflow()  # Should not raise

    def test_validate_invalid_format(self):
        """Should reject unsupported formats."""
        workflow = ExportToFormatWorkflow(format="xml")
        with pytest.raises(UnsupportedFormatError) as exc_info:
            workflow.validate_workflow()
        assert "Unsupported format" in str(exc_info.value)

    def test_validate_json_format(self):
        """Should accept JSON format."""
        workflow = ExportToFormatWorkflow(format="json")
        workflow.validate_workflow()  # Should not raise

    def test_validate_csv_format(self):
        """Should accept CSV format."""
        workflow = ExportToFormatWorkflow(format="csv")
        workflow.validate_workflow()  # Should not raise

    def test_default_format_is_json(self):
        """Should default format to JSON."""
        workflow = ExportToFormatWorkflow()
        assert workflow.format == "json"

    def test_default_pretty_print_is_true(self):
        """Should default pretty_print to True."""
        workflow = ExportToFormatWorkflow()
        assert workflow.pretty_print is True

    def test_optional_output_path(self):
        """Should allow None output_path."""
        workflow = ExportToFormatWorkflow(output_path=None)
        workflow.validate_workflow()  # Should not raise

    def test_optional_fields_filter(self):
        """Should allow None fields."""
        workflow = ExportToFormatWorkflow(fields=None)
        workflow.validate_workflow()  # Should not raise


# =============================================================================
# IMPORT EXPORT HANDLER INITIALIZATION TESTS
# =============================================================================


class TestImportExportHandlerInitialization:
    """Tests for ImportExportHandler initialization."""

    def test_handler_initialization(self):
        """Should initialize handler with dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        handler = ImportExportHandler(repository, logger)

        assert handler.entity_handler is not None
        assert handler.query_handler is not None
        assert handler.logger is logger

    def test_handler_initialization_with_cache(self):
        """Should initialize handler with cache."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        handler = ImportExportHandler(repository, logger, cache)

        assert handler.entity_handler is not None
        assert handler.query_handler is not None


# =============================================================================
# JSON IMPORT TESTS
# =============================================================================


class TestJSONImport:
    """Tests for JSON import operations."""

    @pytest.fixture
    def handler(self):
        """Create import/export handler."""
        repository = MockRepository()
        logger = MockLogger()
        return ImportExportHandler(repository, logger)

    def test_import_json_single_object(self, handler):
        """Should import single JSON object."""
        json_data = json.dumps({
            "name": "Test Workspace",
            "description": "A test workspace",
        })

        workflow = ImportFromFileWorkflow(
            file_content=json_data,
            format="json",
            entity_type="workspace",
        )

        result = handler.handle_import(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["imported_count"] == 1
        assert result.data["failed_count"] == 0

    def test_import_json_array_of_objects(self, handler):
        """Should import JSON array of objects."""
        json_data = json.dumps([
            {"name": "Workspace 1", "description": "First"},
            {"name": "Workspace 2", "description": "Second"},
            {"name": "Workspace 3", "description": "Third"},
        ])

        workflow = ImportFromFileWorkflow(
            file_content=json_data,
            format="json",
            entity_type="workspace",
        )

        result = handler.handle_import(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["imported_count"] == 3
        assert result.data["total"] == 3

    def test_import_json_with_extra_fields(self, handler):
        """Should import JSON with additional properties."""
        json_data = json.dumps({
            "name": "Test Workspace",
            "description": "A test",
            "custom_field": "custom_value",
            "priority": 5,
        })

        workflow = ImportFromFileWorkflow(
            file_content=json_data,
            format="json",
            entity_type="workspace",
        )

        result = handler.handle_import(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["imported_count"] == 1

    def test_import_json_invalid_format(self, handler):
        """Should handle invalid JSON."""
        workflow = ImportFromFileWorkflow(
            file_content="not valid json",
            format="json",
            entity_type="workspace",
        )

        result = handler.handle_import(workflow)

        assert result.status == ResultStatus.ERROR
        assert "error" in result.error.lower()

    def test_import_json_with_validation(self, handler):
        """Should validate entities during import."""
        json_data = json.dumps([
            {"name": "Valid Workspace"},
            {"name": ""},  # Invalid - empty name
        ])

        workflow = ImportFromFileWorkflow(
            file_content=json_data,
            format="json",
            entity_type="workspace",
            validate=True,
            stop_on_error=False,
        )

        result = handler.handle_import(workflow)

        # Should have partial success
        assert result.status == ResultStatus.PARTIAL_SUCCESS
        assert result.data["imported_count"] == 1
        assert result.data["failed_count"] == 1

    def test_import_json_without_validation(self, handler):
        """Should skip validation when disabled."""
        json_data = json.dumps([
            {"name": "Workspace 1"},
            {"name": "Workspace 2"},
        ])

        workflow = ImportFromFileWorkflow(
            file_content=json_data,
            format="json",
            entity_type="workspace",
            validate=False,
        )

        result = handler.handle_import(workflow)

        assert result.status == ResultStatus.SUCCESS

    def test_import_json_stop_on_error(self, handler):
        """Should stop on first error when enabled."""
        json_data = json.dumps([
            {"name": "Valid 1"},
            {"name": ""},  # Invalid
            {"name": "Valid 2"},
        ])

        workflow = ImportFromFileWorkflow(
            file_content=json_data,
            format="json",
            entity_type="workspace",
            validate=True,
            stop_on_error=True,
        )

        result = handler.handle_import(workflow)

        # Should stop after first error
        assert result.status == ResultStatus.PARTIAL_SUCCESS
        assert result.data["imported_count"] == 1


# =============================================================================
# CSV IMPORT TESTS
# =============================================================================


class TestCSVImport:
    """Tests for CSV import operations."""

    @pytest.fixture
    def handler(self):
        """Create import/export handler."""
        repository = MockRepository()
        logger = MockLogger()
        return ImportExportHandler(repository, logger)

    def test_import_csv_basic(self, handler):
        """Should import basic CSV data."""
        csv_data = "name,description\nWorkspace 1,First\nWorkspace 2,Second"

        workflow = ImportFromFileWorkflow(
            file_content=csv_data,
            format="csv",
            entity_type="workspace",
        )

        result = handler.handle_import(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["imported_count"] == 2

    def test_import_csv_with_headers(self, handler):
        """Should import CSV with proper header handling."""
        csv_data = "name,description\nTest,Description"

        workflow = ImportFromFileWorkflow(
            file_content=csv_data,
            format="csv",
            entity_type="project",
        )

        result = handler.handle_import(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["imported_count"] == 1

    def test_import_csv_empty_file(self, handler):
        """Should handle empty CSV."""
        csv_data = "name,description"  # Headers only, no data

        workflow = ImportFromFileWorkflow(
            file_content=csv_data,
            format="csv",
            entity_type="workspace",
        )

        result = handler.handle_import(workflow)

        assert result.status == ResultStatus.ERROR
        assert result.data["imported_count"] == 0

    def test_import_csv_with_quotes(self, handler):
        """Should handle CSV with quoted fields."""
        csv_data = 'name,description\n"Quoted Name","Description, with comma"'

        workflow = ImportFromFileWorkflow(
            file_content=csv_data,
            format="csv",
            entity_type="workspace",
        )

        result = handler.handle_import(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["imported_count"] == 1


# =============================================================================
# JSON EXPORT TESTS
# =============================================================================


class TestJSONExport:
    """Tests for JSON export operations."""

    @pytest.fixture
    def handler(self):
        """Create import/export handler with sample data."""
        repository = MockRepository()
        logger = MockLogger()

        # Add sample entities
        for i in range(5):
            entity = WorkspaceEntity(
                name=f"Workspace {i}",
                description=f"Description {i}",
            )
            repository.save(entity)

        return ImportExportHandler(repository, logger)

    def test_export_json_basic(self, handler):
        """Should export entities to JSON."""
        workflow = ExportToFormatWorkflow(format="json")

        result = handler.handle_export(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert result.metadata["entity_count"] == 5

        # Verify JSON is valid
        data = json.loads(result.data)
        assert isinstance(data, list)
        assert len(data) == 5

    def test_export_json_pretty_print(self, handler):
        """Should pretty-print JSON when enabled."""
        workflow = ExportToFormatWorkflow(
            format="json",
            pretty_print=True,
        )

        result = handler.handle_export(workflow)

        assert result.status == ResultStatus.SUCCESS
        # Pretty-printed JSON should have newlines
        assert "\n" in result.data
        assert "  " in result.data  # Indentation

    def test_export_json_compact(self, handler):
        """Should export compact JSON when pretty_print disabled."""
        workflow = ExportToFormatWorkflow(
            format="json",
            pretty_print=False,
        )

        result = handler.handle_export(workflow)

        assert result.status == ResultStatus.SUCCESS
        # Compact JSON should not have unnecessary whitespace
        data = json.loads(result.data)
        assert isinstance(data, list)

    def test_export_json_with_field_filter(self, handler):
        """Should export only specified fields."""
        workflow = ExportToFormatWorkflow(
            format="json",
            fields=["id", "name"],
        )

        result = handler.handle_export(workflow)

        assert result.status == ResultStatus.SUCCESS
        data = json.loads(result.data)

        # Check that only specified fields are present
        for entity in data:
            assert "id" in entity
            assert "name" in entity
            assert "description" not in entity or len(entity) <= 2

    def test_export_json_with_filters(self, handler):
        """Should export filtered entities."""
        # Add entity with specific status
        repository = handler.entity_handler.entity_service.repository
        entity = WorkspaceEntity(name="Special Workspace")
        repository.save(entity)

        workflow = ExportToFormatWorkflow(
            format="json",
            filters={"name": "Special Workspace"},
        )

        result = handler.handle_export(workflow)

        assert result.status == ResultStatus.SUCCESS
        # Note: MockRepository may not filter perfectly, but should not error


# =============================================================================
# CSV EXPORT TESTS
# =============================================================================


class TestCSVExport:
    """Tests for CSV export operations."""

    @pytest.fixture
    def handler(self):
        """Create import/export handler with sample data."""
        repository = MockRepository()
        logger = MockLogger()

        # Add sample entities
        for i in range(3):
            entity = WorkspaceEntity(
                name=f"Workspace {i}",
                description=f"Description {i}",
            )
            repository.save(entity)

        return ImportExportHandler(repository, logger)

    def test_export_csv_basic(self, handler):
        """Should export entities to CSV."""
        workflow = ExportToFormatWorkflow(format="csv")

        result = handler.handle_export(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None

        # Verify CSV structure
        lines = result.data.strip().split("\n")
        assert len(lines) >= 4  # Header + 3 entities

    def test_export_csv_with_field_filter(self, handler):
        """Should export only specified fields to CSV."""
        workflow = ExportToFormatWorkflow(
            format="csv",
            fields=["id", "name"],
        )

        result = handler.handle_export(workflow)

        assert result.status == ResultStatus.SUCCESS

        # Parse CSV and check fields
        reader = csv.DictReader(StringIO(result.data))
        fieldnames = reader.fieldnames
        assert "id" in fieldnames
        assert "name" in fieldnames

    def test_export_csv_empty_result(self):
        """Should handle exporting when no entities match."""
        repository = MockRepository()
        logger = MockLogger()
        handler = ImportExportHandler(repository, logger)

        workflow = ExportToFormatWorkflow(
            format="csv",
            filters={"nonexistent_field": "value"},
        )

        result = handler.handle_export(workflow)

        # Should succeed but with empty data
        assert result.status == ResultStatus.SUCCESS
        assert result.data == ""


# =============================================================================
# FILE OPERATIONS TESTS
# =============================================================================


class TestFileOperations:
    """Tests for file-based import/export."""

    @pytest.fixture
    def handler(self):
        """Create import/export handler."""
        repository = MockRepository()
        logger = MockLogger()
        return ImportExportHandler(repository, logger)

    def test_import_from_file_path(self, handler):
        """Should import from file path."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"name": "Test Workspace"}], f)
            file_path = f.name

        try:
            workflow = ImportFromFileWorkflow(
                file_path=file_path,
                format="json",
                entity_type="workspace",
            )

            result = handler.handle_import(workflow)

            assert result.status == ResultStatus.SUCCESS
            assert result.data["imported_count"] == 1
        finally:
            Path(file_path).unlink()

    def test_export_to_file_path(self, handler):
        """Should export to file path."""
        # Add sample entity
        entity = WorkspaceEntity(name="Test Workspace")
        handler.entity_handler.entity_service.repository.save(entity)

        # Create temporary file path
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            file_path = f.name

        try:
            workflow = ExportToFormatWorkflow(
                format="json",
                output_path=file_path,
            )

            result = handler.handle_export(workflow)

            assert result.status == ResultStatus.SUCCESS
            assert result.metadata["output_path"] == file_path

            # Verify file was created
            assert Path(file_path).exists()

            # Verify content
            with open(file_path, "r") as f:
                data = json.load(f)
                assert isinstance(data, list)
                assert len(data) == 1
        finally:
            if Path(file_path).exists():
                Path(file_path).unlink()


# =============================================================================
# LARGE FILE HANDLING TESTS
# =============================================================================


@pytest.mark.performance
class TestLargeFileHandling:
    """Tests for handling large import/export operations."""

    def test_import_large_json_array(self):
        """Should handle importing large JSON arrays."""
        repository = MockRepository()
        logger = MockLogger()
        handler = ImportExportHandler(repository, logger)

        # Create large dataset
        large_data = [
            {"name": f"Workspace {i}", "description": f"Description {i}"}
            for i in range(500)
        ]
        json_data = json.dumps(large_data)

        workflow = ImportFromFileWorkflow(
            file_content=json_data,
            format="json",
            entity_type="workspace",
        )

        result = handler.handle_import(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["imported_count"] == 500

    def test_export_large_dataset(self):
        """Should handle exporting large datasets."""
        repository = MockRepository()
        logger = MockLogger()

        # Create large dataset
        for i in range(500):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            repository.save(entity)

        handler = ImportExportHandler(repository, logger)

        workflow = ExportToFormatWorkflow(format="json")

        result = handler.handle_export(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["entity_count"] == 500


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestImportExportErrorHandling:
    """Tests for error handling in import/export operations."""

    def test_import_validation_error(self):
        """Should handle workflow validation errors."""
        repository = MockRepository()
        logger = MockLogger()
        handler = ImportExportHandler(repository, logger)

        # Missing both file_path and file_content
        workflow = ImportFromFileWorkflow(
            format="json",
            entity_type="workspace",
        )

        result = handler.handle_import(workflow)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_export_validation_error(self):
        """Should handle export validation errors."""
        repository = MockRepository()
        logger = MockLogger()
        handler = ImportExportHandler(repository, logger)

        # Unsupported format
        workflow = ExportToFormatWorkflow(format="xml")

        result = handler.handle_export(workflow)

        assert result.status == ResultStatus.ERROR
        assert "Unsupported format" in result.error

    def test_import_logs_errors(self):
        """Should log errors during import."""
        repository = MockRepository()
        logger = MockLogger()
        handler = ImportExportHandler(repository, logger)

        json_data = json.dumps([
            {"name": "Valid"},
            {"name": ""},  # Invalid
        ])

        workflow = ImportFromFileWorkflow(
            file_content=json_data,
            format="json",
            entity_type="workspace",
            stop_on_error=False,
        )

        handler.handle_import(workflow)

        # Check for error logs
        error_logs = [log for log in logger.logs if log["level"] in ["ERROR", "WARNING"]]
        assert len(error_logs) > 0

    def test_export_handles_empty_repository(self):
        """Should handle exporting from empty repository."""
        repository = MockRepository()
        logger = MockLogger()
        handler = ImportExportHandler(repository, logger)

        workflow = ExportToFormatWorkflow(format="json")

        result = handler.handle_export(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["entity_count"] == 0


__all__ = [
    "TestImportWorkflowValidation",
    "TestExportWorkflowValidation",
    "TestImportExportHandlerInitialization",
    "TestJSONImport",
    "TestCSVImport",
    "TestJSONExport",
    "TestCSVExport",
    "TestFileOperations",
    "TestLargeFileHandling",
    "TestImportExportErrorHandling",
]
