"""
Output formatters for CLI commands.

This module provides formatters for different output formats:
- table: Rich tables for terminal display
- json: JSON output
- yaml: YAML output
- csv: CSV output
"""

import csv
import io
import json
from typing import Any, Union

try:
    import yaml
    from rich.table import Table
except ImportError:
    yaml = None
    Table = None


class BaseFormatter:
    """Base formatter with common functionality."""

    def format_single(self, data: dict[str, Any], output_format: str = "table") -> str:
        """
        Format single entity/item.

        Args:
            data: Data to format
            output_format: Output format (table, json, yaml, csv)

        Returns:
            Formatted output string
        """
        if output_format == "json":
            return self._format_json(data)
        elif output_format == "yaml":
            return self._format_yaml(data)
        elif output_format == "csv":
            return self._format_csv([data])
        else:
            return self._format_table_single(data)

    def format_list(
        self, data: dict[str, Any], output_format: str = "table"
    ) -> Union[str, Table]:
        """
        Format list of entities/items.

        Args:
            data: Data with list in 'data' key
            output_format: Output format

        Returns:
            Formatted output
        """
        items = data.get("data", [])

        if output_format == "json":
            return self._format_json(data)
        elif output_format == "yaml":
            return self._format_yaml(data)
        elif output_format == "csv":
            return self._format_csv(items)
        else:
            return self._format_table_list(items, data)

    def _format_json(self, data: Any) -> str:
        """Format as JSON."""
        return json.dumps(data, indent=2, default=str)

    def _format_yaml(self, data: Any) -> str:
        """Format as YAML."""
        if yaml is None:
            raise ImportError("PyYAML is required for YAML output")
        return yaml.dump(data, default_flow_style=False)

    def _format_csv(self, items: list[dict[str, Any]]) -> str:
        """Format as CSV."""
        if not items:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=items[0].keys())
        writer.writeheader()
        writer.writerows(items)
        return output.getvalue()

    def _format_table_single(self, data: dict[str, Any]) -> Table:
        """Format single item as table - to be implemented by subclasses."""
        raise NotImplementedError

    def _format_table_list(
        self, items: list[dict[str, Any]], metadata: dict[str, Any]
    ) -> Table:
        """Format list as table - to be implemented by subclasses."""
        raise NotImplementedError


class EntityFormatter(BaseFormatter):
    """Formatter for entity data."""

    def _format_table_single(self, data: dict[str, Any]) -> Table:
        """Format single entity as table."""
        if Table is None:
            raise ImportError("rich is required for table output")

        entity = data.get("data", {})

        table = Table(title="Entity Details", show_header=True)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        # Add key fields
        fields = [
            ("ID", entity.get("id")),
            ("Type", entity.get("entity_type")),
            ("Name", entity.get("name")),
            ("Description", entity.get("description")),
            ("Status", entity.get("status")),
            ("Created", entity.get("created_at")),
            ("Updated", entity.get("updated_at")),
        ]

        for field, value in fields:
            if value:
                table.add_row(field, str(value))

        # Add properties if present
        properties = entity.get("properties", {})
        if properties:
            table.add_section()
            table.add_row("[bold]Properties[/bold]", "")
            for key, value in properties.items():
                table.add_row(f"  {key}", str(value))

        return table

    def _format_table_list(
        self, items: list[dict[str, Any]], metadata: dict[str, Any]
    ) -> Table:
        """Format entity list as table."""
        if Table is None:
            raise ImportError("rich is required for table output")

        table = Table(title="Entities", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Type", style="blue")
        table.add_column("Name", style="white")
        table.add_column("Status", style="green")
        table.add_column("Created", style="dim")

        for item in items:
            table.add_row(
                item.get("id", "")[:12] + "...",
                item.get("entity_type", ""),
                item.get("name", ""),
                item.get("status", ""),
                str(item.get("created_at", ""))[:10],
            )

        # Add pagination info
        total = metadata.get("total_count", 0)
        page = metadata.get("page", 1)
        page_size = metadata.get("page_size", 20)
        table.caption = f"Showing {len(items)} of {total} (Page {page})"

        return table


class RelationshipFormatter(BaseFormatter):
    """Formatter for relationship data."""

    def _format_table_single(self, data: dict[str, Any]) -> Table:
        """Format single relationship as table."""
        if Table is None:
            raise ImportError("rich is required for table output")

        relationship = data.get("data", {})

        table = Table(title="Relationship Details", show_header=True)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        fields = [
            ("ID", relationship.get("id")),
            ("Source ID", relationship.get("source_id")),
            ("Target ID", relationship.get("target_id")),
            ("Type", relationship.get("relationship_type")),
            ("Status", relationship.get("status")),
            ("Created", relationship.get("created_at")),
        ]

        for field, value in fields:
            if value:
                table.add_row(field, str(value))

        # Add properties if present
        properties = relationship.get("properties", {})
        if properties:
            table.add_section()
            table.add_row("[bold]Properties[/bold]", "")
            for key, value in properties.items():
                table.add_row(f"  {key}", str(value))

        return table

    def _format_table_list(
        self, items: list[dict[str, Any]], metadata: dict[str, Any]
    ) -> Table:
        """Format relationship list as table."""
        if Table is None:
            raise ImportError("rich is required for table output")

        table = Table(title="Relationships", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Source", style="blue")
        table.add_column("→", style="white")
        table.add_column("Target", style="blue")
        table.add_column("Type", style="green")

        for item in items:
            table.add_row(
                item.get("id", "")[:12] + "...",
                item.get("source_id", "")[:12] + "...",
                "→",
                item.get("target_id", "")[:12] + "...",
                item.get("relationship_type", ""),
            )

        table.caption = f"Showing {len(items)} relationships"
        return table


class WorkflowFormatter(BaseFormatter):
    """Formatter for workflow data."""

    def _format_table_single(self, data: dict[str, Any]) -> Table:
        """Format single workflow as table."""
        if Table is None:
            raise ImportError("rich is required for table output")

        workflow = data.get("data", {})

        table = Table(title="Workflow Details", show_header=True)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        fields = [
            ("ID", workflow.get("id")),
            ("Name", workflow.get("name")),
            ("Description", workflow.get("description")),
            ("Trigger", workflow.get("trigger_type")),
            ("Enabled", "✓" if workflow.get("enabled") else "✗"),
            ("Steps", len(workflow.get("steps", []))),
            ("Created", workflow.get("created_at")),
        ]

        for field, value in fields:
            if value is not None:
                table.add_row(field, str(value))

        return table

    def _format_table_list(
        self, items: list[dict[str, Any]], metadata: dict[str, Any]
    ) -> Table:
        """Format workflow list as table."""
        if Table is None:
            raise ImportError("rich is required for table output")

        table = Table(title="Workflows", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Trigger", style="blue")
        table.add_column("Steps", style="green")
        table.add_column("Enabled", style="yellow")

        for item in items:
            table.add_row(
                item.get("id", "")[:12] + "...",
                item.get("name", ""),
                item.get("trigger_type", ""),
                str(len(item.get("steps", []))),
                "✓" if item.get("enabled") else "✗",
            )

        table.caption = f"Showing {len(items)} workflows"
        return table


class StatsFormatter(BaseFormatter):
    """Formatter for statistics and analytics data."""

    def format_workspace_stats(
        self, data: dict[str, Any], output_format: str = "table"
    ) -> Union[str, Table]:
        """Format workspace statistics."""
        if output_format == "json":
            return self._format_json(data)
        elif output_format == "yaml":
            return self._format_yaml(data)
        else:
            return self._format_workspace_stats_table(data)

    def _format_workspace_stats_table(self, data: dict[str, Any]) -> Table:
        """Format workspace stats as table."""
        if Table is None:
            raise ImportError("rich is required for table output")

        stats = data.get("data", {})

        table = Table(title="Workspace Statistics", show_header=True)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        # Entity counts
        entity_counts = stats.get("entity_counts", {})
        table.add_row("[bold]Entity Counts[/bold]", "")
        for entity_type, count in entity_counts.items():
            table.add_row(f"  {entity_type}", str(count))

        # Status breakdown
        table.add_section()
        status_counts = stats.get("status_counts", {})
        table.add_row("[bold]Status Breakdown[/bold]", "")
        for status, count in status_counts.items():
            table.add_row(f"  {status}", str(count))

        # Relationship counts
        table.add_section()
        relationship_counts = stats.get("relationship_counts", {})
        table.add_row("[bold]Relationships[/bold]", "")
        for rel_type, count in relationship_counts.items():
            table.add_row(f"  {rel_type}", str(count))

        return table

    def _format_table_single(self, data: dict[str, Any]) -> Table:
        """Not used for stats formatter."""
        return self._format_workspace_stats_table(data)

    def _format_table_list(
        self, items: list[dict[str, Any]], metadata: dict[str, Any]
    ) -> Table:
        """Not used for stats formatter."""
        if Table is None:
            raise ImportError("rich is required for table output")
        table = Table(title="Statistics")
        table.add_column("Stats", style="cyan")
        return table


__all__ = [
    "BaseFormatter",
    "EntityFormatter",
    "RelationshipFormatter",
    "WorkflowFormatter",
    "StatsFormatter",
]
