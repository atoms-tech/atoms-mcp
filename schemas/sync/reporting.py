"""
Reporting utilities for schema synchronization.

This module contains methods for generating reports, printing differences,
and displaying schema synchronization results.
"""

from datetime import datetime
from pathlib import Path
from typing import Any
from .base import Colors


class SchemaReporter:
    """Handles reporting and display operations for schema synchronization."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def print_diff(self, differences: list[dict[str, Any]]):
        """Print detailed diff of schema changes."""
        if not differences:
            print(f"{Colors.GREEN}✓ No schema differences found{Colors.END}")
            return

        print(f"\n{Colors.BOLD}Schema Differences:{Colors.END}\n")

        for diff in differences:
            severity_color = {
                "critical": Colors.RED,
                "high": Colors.YELLOW,
                "medium": Colors.BLUE,
                "low": Colors.GREEN
            }.get(diff.get("severity", "low"), Colors.END)

            print(f"{severity_color}[{diff['severity'].upper()}] {diff['type'].upper()}: {diff['name']}{Colors.END}")
            print(f"  Change: {diff['change']}")

            if diff["change"] == "added":
                if diff["type"] == "enum":
                    print(f"  Values: {', '.join(diff['values'])}")
                elif diff["type"] == "table":
                    print(f"  Columns: {len(diff['columns'])}")

            elif diff["change"] == "modified":
                if "added_values" in diff:
                    print(f"  Added values: {', '.join(diff['added_values'])}")
                if "removed_values" in diff:
                    print(f"  Removed values: {', '.join(diff['removed_values'])}")
                if "added_columns" in diff:
                    print(f"  Added columns: {', '.join(diff['added_columns'])}")
                if "removed_columns" in diff:
                    print(f"  Removed columns: {', '.join(diff['removed_columns'])}")

            print()

    def generate_report(self, differences: list[dict[str, Any]], db_schema: dict[str, Any], calculate_schema_hash)
        """Generate a detailed markdown report."""
        report_file = self.root_dir / f"schema_drift_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(report_file, "w") as f:
            f.write("# Schema Drift Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Database Hash:** {calculate_schema_hash(db_schema)}\n\n")

            if not differences:
                f.write("## Status: ✓ No Drift Detected\n\n")
                f.write("Local schemas are in sync with database.\n")
            else:
                f.write(f"## Status: ⚠️ {len(differences)} Differences Found\n\n")
                
                # Group by type
                enums = [d for d in differences if d["type"] == "enum"]
                tables = [d for d in differences if d["type"] == "table"]
                
                if enums:
                    f.write("### Enum Changes\n\n")
                    for diff in enums:
                        f.write(f"- **{diff['name']}** ({diff['change']})\n")
                        if diff["change"] == "added":
                            f.write(f"  - Values: {', '.join(diff['values'])}\n")
                        elif diff["change"] == "modified":
                            if "added_values" in diff:
                                f.write(f"  - Added: {', '.join(diff['added_values'])}\n")
                            if "removed_values" in diff:
                                f.write(f"  - Removed: {', '.join(diff['removed_values'])}\n")
                        f.write("\n")
                
                if tables:
                    f.write("### Table Changes\n\n")
                    for diff in tables:
                        f.write(f"- **{diff['name']}** ({diff['change']})\n")
                        if diff["change"] == "added":
                            f.write(f"  - Columns: {len(diff['columns'])}\n")
                        elif diff["change"] == "modified":
                            if "added_columns" in diff:
                                f.write(f"  - Added columns: {', '.join(diff['added_columns'])}\n")
                            if "removed_columns" in diff:
                                f.write(f"  - Removed columns: {', '.join(diff['removed_columns'])}\n")
                        f.write("\n")

        print(f"{Colors.BLUE}📊 Report saved: {report_file.relative_to(self.root_dir)}{Colors.END}")
        return report_file