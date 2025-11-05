"""
Import/export workflows for the application layer.

This module implements workflows for importing and exporting entities
in various formats (JSON, CSV, etc.).
"""

import csv
import json
from dataclasses import dataclass, field
from io import StringIO
from typing import Any, Optional

from ...domain.models.entity import Entity
from ...domain.ports.cache import Cache
from ...domain.ports.logger import Logger
from ...domain.ports.repository import Repository
from ..commands.entity_commands import CreateEntityCommand, EntityCommandHandler
from ..dto import CommandResult, ResultStatus
from ..queries.entity_queries import EntityQueryHandler, ListEntitiesQuery


class ImportExportError(Exception):
    """Base exception for import/export errors."""

    pass


class ImportExportValidationError(ImportExportError):
    """Exception raised for import/export validation failures."""

    pass


class UnsupportedFormatError(ImportExportError):
    """Exception raised for unsupported file formats."""

    pass


@dataclass
class ImportFromFileWorkflow:
    """
    Workflow for importing entities from a file.

    Attributes:
        file_path: Path to file to import (optional if file_content provided)
        file_content: File content as string (optional if file_path provided)
        format: File format ("json" or "csv")
        entity_type: Default entity type for imported entities
        validate: Whether to validate entities before import
        stop_on_error: Whether to stop on first error
    """

    file_path: Optional[str] = None
    file_content: Optional[str] = None
    format: str = "json"
    entity_type: str = "entity"
    validate: bool = True
    stop_on_error: bool = False

    def validate_workflow(self) -> None:
        """
        Validate workflow parameters.

        Raises:
            ImportExportValidationError: If validation fails
        """
        if not self.file_path and not self.file_content:
            raise ImportExportValidationError(
                "Either file_path or file_content must be provided"
            )

        if self.format not in ("json", "csv"):
            raise UnsupportedFormatError(
                f"Unsupported format: {self.format}. Supported formats: json, csv"
            )

        if not self.entity_type:
            raise ImportExportValidationError("entity_type is required")


@dataclass
class ExportToFormatWorkflow:
    """
    Workflow for exporting entities to a file.

    Attributes:
        output_path: Path to output file (optional, returns string if not provided)
        format: Output format ("json" or "csv")
        filters: Optional filters for entity selection
        fields: Optional list of fields to export (None = all fields)
        pretty_print: Whether to pretty-print JSON output
    """

    output_path: Optional[str] = None
    format: str = "json"
    filters: dict[str, Any] = field(default_factory=dict)
    fields: Optional[list[str]] = None
    pretty_print: bool = True

    def validate_workflow(self) -> None:
        """
        Validate workflow parameters.

        Raises:
            ImportExportValidationError: If validation fails
        """
        if self.format not in ("json", "csv"):
            raise UnsupportedFormatError(
                f"Unsupported format: {self.format}. Supported formats: json, csv"
            )


class ImportExportHandler:
    """
    Handler for import/export workflows.

    This class handles importing and exporting entities in various formats
    with proper validation and error handling.

    Attributes:
        entity_handler: Command handler for entity operations
        query_handler: Query handler for entity retrieval
        logger: Logger for recording events
    """

    def __init__(
        self,
        repository: Repository[Entity],
        logger: Logger,
        cache: Optional[Cache] = None,
    ):
        """
        Initialize import/export handler.

        Args:
            repository: Repository for entity persistence
            logger: Logger for recording events
            cache: Optional cache for performance
        """
        self.entity_handler = EntityCommandHandler(repository, logger, cache)
        self.query_handler = EntityQueryHandler(repository, logger, cache)
        self.logger = logger

    def handle_import(
        self, workflow: ImportFromFileWorkflow
    ) -> CommandResult[dict[str, Any]]:
        """
        Handle import from file workflow.

        Args:
            workflow: Import workflow

        Returns:
            Command result with import statistics
        """
        try:
            # Validate workflow
            workflow.validate_workflow()

            self.logger.info(f"Starting import from {workflow.format} format")

            # Read file content
            if workflow.file_content:
                content = workflow.file_content
            else:
                with open(workflow.file_path, "r") as f:
                    content = f.read()

            # Parse content based on format
            if workflow.format == "json":
                entities_data = self._parse_json(content)
            elif workflow.format == "csv":
                entities_data = self._parse_csv(content)
            else:
                raise UnsupportedFormatError(f"Unsupported format: {workflow.format}")

            self.logger.info(f"Parsed {len(entities_data)} entities from file")

            # Import entities
            imported = []
            failed = []
            errors = []

            for i, entity_data in enumerate(entities_data):
                try:
                    # Create entity command
                    command = self._create_entity_command(entity_data, workflow.entity_type)

                    # Validate if requested
                    if workflow.validate:
                        command.validate()

                    # Create entity
                    result = self.entity_handler.handle_create_entity(command)

                    if result.is_success:
                        imported.append(result.data.id)
                        self.logger.debug(
                            f"Imported entity {i + 1}/{len(entities_data)}"
                        )
                    else:
                        failed.append(i)
                        errors.append(f"Entity {i}: {result.error}")
                        self.logger.warning(
                            f"Failed to import entity {i + 1}: {result.error}"
                        )

                        if workflow.stop_on_error:
                            break

                except Exception as e:
                    failed.append(i)
                    errors.append(f"Entity {i}: {str(e)}")
                    self.logger.error(f"Unexpected error importing entity {i + 1}: {e}")

                    if workflow.stop_on_error:
                        break

            # Determine result status
            if not imported:
                status = ResultStatus.ERROR
            elif failed:
                status = ResultStatus.PARTIAL_SUCCESS
            else:
                status = ResultStatus.SUCCESS

            self.logger.info(
                f"Import completed: {len(imported)} imported, {len(failed)} failed"
            )

            result_data = {
                "imported_count": len(imported),
                "failed_count": len(failed),
                "imported_ids": imported,
                "total": len(entities_data),
            }

            return CommandResult(
                status=status,
                data=result_data,
                error="; ".join(errors) if errors else None,
                metadata={
                    "format": workflow.format,
                    "entity_type": workflow.entity_type,
                },
            )

        except ImportExportValidationError as e:
            self.logger.error(f"Import validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except UnsupportedFormatError as e:
            self.logger.error(f"Unsupported format: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=str(e),
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during import: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_export(
        self, workflow: ExportToFormatWorkflow
    ) -> CommandResult[str]:
        """
        Handle export to format workflow.

        Args:
            workflow: Export workflow

        Returns:
            Command result with exported content
        """
        try:
            # Validate workflow
            workflow.validate_workflow()

            self.logger.info(f"Starting export to {workflow.format} format")

            # Query entities
            query = ListEntitiesQuery(
                filters=workflow.filters,
                limit=10000,  # Max export limit
            )

            result = self.query_handler.handle_list_entities(query)

            if not result.is_success:
                raise ImportExportError(f"Failed to query entities: {result.error}")

            entities = result.data
            self.logger.info(f"Retrieved {len(entities)} entities for export")

            # Export based on format
            if workflow.format == "json":
                content = self._export_json(
                    entities, workflow.fields, workflow.pretty_print
                )
            elif workflow.format == "csv":
                content = self._export_csv(entities, workflow.fields)
            else:
                raise UnsupportedFormatError(f"Unsupported format: {workflow.format}")

            # Write to file if path provided
            if workflow.output_path:
                with open(workflow.output_path, "w") as f:
                    f.write(content)
                self.logger.info(f"Exported to file: {workflow.output_path}")

            self.logger.info("Export completed successfully")

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=content,
                metadata={
                    "format": workflow.format,
                    "entity_count": len(entities),
                    "output_path": workflow.output_path,
                },
            )

        except ImportExportValidationError as e:
            self.logger.error(f"Export validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except UnsupportedFormatError as e:
            self.logger.error(f"Unsupported format: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=str(e),
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during export: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def _parse_json(self, content: str) -> list[dict[str, Any]]:
        """Parse JSON content."""
        data = json.loads(content)

        # Handle both single object and array
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            raise ImportExportValidationError(
                "JSON must be an object or array of objects"
            )

    def _parse_csv(self, content: str) -> list[dict[str, Any]]:
        """Parse CSV content."""
        reader = csv.DictReader(StringIO(content))
        return list(reader)

    def _create_entity_command(
        self, entity_data: dict[str, Any], default_entity_type: str
    ) -> CreateEntityCommand:
        """Create entity command from data."""
        entity_type = entity_data.get("entity_type", default_entity_type)
        name = entity_data.get("name", entity_data.get("title", "Unnamed"))
        description = entity_data.get("description", "")

        # Extract properties (all fields except known command fields)
        command_fields = {"entity_type", "name", "title", "description", "metadata"}
        properties = {
            k: v for k, v in entity_data.items() if k not in command_fields
        }

        return CreateEntityCommand(
            entity_type=entity_type,
            name=name,
            description=description,
            properties=properties,
            metadata=entity_data.get("metadata", {}),
        )

    def _export_json(
        self, entities: list[Any], fields: Optional[list[str]], pretty_print: bool
    ) -> str:
        """Export entities to JSON."""
        entities_data = []

        for entity in entities:
            entity_dict = entity.to_dict()

            # Filter fields if specified
            if fields:
                entity_dict = {k: v for k, v in entity_dict.items() if k in fields}

            entities_data.append(entity_dict)

        if pretty_print:
            return json.dumps(entities_data, indent=2, default=str)
        else:
            return json.dumps(entities_data, default=str)

    def _export_csv(
        self, entities: list[Any], fields: Optional[list[str]]
    ) -> str:
        """Export entities to CSV."""
        if not entities:
            return ""

        # Determine fields to export
        if fields:
            fieldnames = fields
        else:
            # Use all fields from first entity
            first_entity = entities[0].to_dict()
            fieldnames = list(first_entity.keys())

        # Create CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for entity in entities:
            entity_dict = entity.to_dict()

            # Filter and flatten nested structures
            row = {}
            for field in fieldnames:
                value = entity_dict.get(field)
                if isinstance(value, (dict, list)):
                    row[field] = json.dumps(value)
                else:
                    row[field] = str(value) if value is not None else ""

            writer.writerow(row)

        return output.getvalue()


__all__ = [
    "ImportFromFileWorkflow",
    "ExportToFormatWorkflow",
    "ImportExportHandler",
    "ImportExportError",
    "ImportExportValidationError",
    "UnsupportedFormatError",
]
