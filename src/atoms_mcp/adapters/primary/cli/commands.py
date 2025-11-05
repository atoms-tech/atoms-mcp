"""
Typer CLI application for Atoms.

This module provides a modern CLI interface using Typer framework.
It replaces the old CLI files with a unified, well-structured command system.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import typer
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
except ImportError:
    print("Error: typer and rich are required. Install with: pip install typer rich")
    sys.exit(1)

from .formatters import (
    EntityFormatter,
    RelationshipFormatter,
    StatsFormatter,
    WorkflowFormatter,
)
from .handlers import CLIHandlers

# Create CLI app
app = typer.Typer(
    name="atoms",
    help="Atoms MCP CLI - Manage your workspace entities, relationships, and workflows",
    add_completion=True,
    rich_markup_mode="rich",
)

# Create console for rich output
console = Console()

# Subcommands
entity_app = typer.Typer(help="Manage entities")
relationship_app = typer.Typer(help="Manage relationships")
workflow_app = typer.Typer(help="Manage workflows")
workspace_app = typer.Typer(help="Manage workspaces")
config_app = typer.Typer(help="Manage configuration")

app.add_typer(entity_app, name="entity")
app.add_typer(relationship_app, name="relationship")
app.add_typer(workflow_app, name="workflow")
app.add_typer(workspace_app, name="workspace")
app.add_typer(config_app, name="config")


# Initialize handlers
def get_handlers() -> CLIHandlers:
    """Get CLI handlers with environment configuration."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        console.print("[yellow]Warning: Supabase credentials not found. Using in-memory storage.[/yellow]")

    return CLIHandlers(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
    )


# Entity Commands
@entity_app.command("create")
def entity_create(
    entity_type: str = typer.Argument(..., help="Type of entity (workspace, project, task, document)"),
    name: str = typer.Argument(..., help="Entity name"),
    description: str = typer.Option("", "--description", "-d", help="Entity description"),
    properties: str = typer.Option("{}", "--properties", "-p", help="JSON properties"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format (table, json, yaml, csv)"),
) -> None:
    """Create a new entity."""
    handlers = get_handlers()

    try:
        props = json.loads(properties) if properties != "{}" else {}
        result = handlers.create_entity(entity_type, name, description, props)

        formatter = EntityFormatter()
        output = formatter.format_single(result, output_format)
        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@entity_app.command("get")
def entity_get(
    entity_id: str = typer.Argument(..., help="Entity ID"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format"),
) -> None:
    """Get entity by ID."""
    handlers = get_handlers()

    try:
        result = handlers.get_entity(entity_id)

        formatter = EntityFormatter()
        output = formatter.format_single(result, output_format)
        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@entity_app.command("list")
def entity_list(
    entity_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by entity type"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format"),
) -> None:
    """List entities with filtering."""
    handlers = get_handlers()

    try:
        filters = {}
        if entity_type:
            filters["entity_type"] = entity_type
        if status:
            filters["status"] = status

        result = handlers.list_entities(filters, limit)

        formatter = EntityFormatter()
        output = formatter.format_list(result, output_format)
        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@entity_app.command("update")
def entity_update(
    entity_id: str = typer.Argument(..., help="Entity ID"),
    updates: str = typer.Argument(..., help="JSON updates"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format"),
) -> None:
    """Update an entity."""
    handlers = get_handlers()

    try:
        update_data = json.loads(updates)
        result = handlers.update_entity(entity_id, update_data)

        formatter = EntityFormatter()
        output = formatter.format_single(result, output_format)
        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@entity_app.command("delete")
def entity_delete(
    entity_id: str = typer.Argument(..., help="Entity ID"),
    soft: bool = typer.Option(True, "--soft/--hard", help="Soft or hard delete"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Delete an entity."""
    handlers = get_handlers()

    if not confirm:
        confirmed = typer.confirm(f"Are you sure you want to delete entity {entity_id}?")
        if not confirmed:
            console.print("Aborted.")
            raise typer.Exit(0)

    try:
        handlers.delete_entity(entity_id, soft)
        console.print(f"[green]Successfully deleted entity {entity_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# Relationship Commands
@relationship_app.command("create")
def relationship_create(
    source_id: str = typer.Argument(..., help="Source entity ID"),
    target_id: str = typer.Argument(..., help="Target entity ID"),
    relationship_type: str = typer.Argument(..., help="Relationship type"),
    properties: str = typer.Option("{}", "--properties", "-p", help="JSON properties"),
    bidirectional: bool = typer.Option(False, "--bidirectional", "-b", help="Create inverse relationship"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format"),
) -> None:
    """Create a relationship between entities."""
    handlers = get_handlers()

    try:
        props = json.loads(properties) if properties != "{}" else {}
        result = handlers.create_relationship(source_id, target_id, relationship_type, props, bidirectional)

        formatter = RelationshipFormatter()
        output = formatter.format_single(result, output_format)
        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@relationship_app.command("list")
def relationship_list(
    source_id: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by source"),
    target_id: Optional[str] = typer.Option(None, "--target", "-t", help="Filter by target"),
    relationship_type: Optional[str] = typer.Option(None, "--type", help="Filter by type"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format"),
) -> None:
    """List relationships."""
    handlers = get_handlers()

    try:
        result = handlers.list_relationships(source_id, target_id, relationship_type)

        formatter = RelationshipFormatter()
        output = formatter.format_list(result, output_format)
        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@relationship_app.command("delete")
def relationship_delete(
    relationship_id: str = typer.Argument(..., help="Relationship ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Delete a relationship."""
    handlers = get_handlers()

    if not confirm:
        confirmed = typer.confirm(f"Are you sure you want to delete relationship {relationship_id}?")
        if not confirmed:
            console.print("Aborted.")
            raise typer.Exit(0)

    try:
        handlers.delete_relationship(relationship_id)
        console.print(f"[green]Successfully deleted relationship {relationship_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# Workflow Commands
@workflow_app.command("create")
def workflow_create(
    name: str = typer.Argument(..., help="Workflow name"),
    description: str = typer.Option("", "--description", "-d", help="Workflow description"),
    trigger_type: str = typer.Option("manual", "--trigger", "-t", help="Trigger type"),
    steps_file: Optional[Path] = typer.Option(None, "--steps", "-s", help="JSON file with workflow steps"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format"),
) -> None:
    """Create a new workflow."""
    handlers = get_handlers()

    try:
        steps = []
        if steps_file:
            steps = json.loads(steps_file.read_text())

        result = handlers.create_workflow(name, description, trigger_type, steps)

        formatter = WorkflowFormatter()
        output = formatter.format_single(result, output_format)
        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@workflow_app.command("execute")
def workflow_execute(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
    parameters: str = typer.Option("{}", "--params", "-p", help="JSON parameters"),
    async_exec: bool = typer.Option(False, "--async", "-a", help="Execute asynchronously"),
) -> None:
    """Execute a workflow."""
    handlers = get_handlers()

    try:
        params = json.loads(parameters) if parameters != "{}" else {}
        result = handlers.execute_workflow(workflow_id, params, async_exec)

        if async_exec:
            console.print(f"[green]Workflow execution started: {result['data']['execution_id']}[/green]")
        else:
            console.print("[green]Workflow execution completed successfully[/green]")
            console.print(json.dumps(result, indent=2))

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@workflow_app.command("list")
def workflow_list(
    enabled_only: bool = typer.Option(False, "--enabled", "-e", help="Show only enabled workflows"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format"),
) -> None:
    """List workflows."""
    handlers = get_handlers()

    try:
        result = handlers.list_workflows(enabled_only)

        formatter = WorkflowFormatter()
        output = formatter.format_list(result, output_format)
        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# Workspace Commands
@workspace_app.command("stats")
def workspace_stats(
    workspace_id: str = typer.Argument(..., help="Workspace ID"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format"),
) -> None:
    """Get workspace statistics."""
    handlers = get_handlers()

    try:
        result = handlers.get_workspace_stats(workspace_id)

        formatter = StatsFormatter()
        output = formatter.format_workspace_stats(result, output_format)
        console.print(output)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# Config Commands
@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    console.print("[bold]Current Configuration:[/bold]")
    console.print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', '[red]Not set[/red]')}")
    console.print(f"SUPABASE_KEY: {'***' if os.getenv('SUPABASE_KEY') else '[red]Not set[/red]'}")


@app.command()
def version() -> None:
    """Show version information."""
    console.print("[bold]Atoms MCP CLI[/bold] version 0.1.0")


def main() -> None:
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()


__all__ = ["app", "main"]
