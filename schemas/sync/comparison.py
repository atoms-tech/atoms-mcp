"""
Schema comparison utilities for schema synchronization.

This module contains methods for comparing database schemas with local schemas
and identifying differences, including enum and table changes.
"""

from typing import Any


class SchemaComparator:
    """Handles schema comparison operations."""
    
    def __init__(self):
        # Filter out system enums (Supabase auth schema enums)
        self.system_enums = {
            "key_status", "key_type", "aal_level", "code_challenge_method",
            "factor_status", "factor_type", "one_time_token_type",
            "request_status", "equality_op", "action", "buckettype",
            "oauth_registration_type"
        }

    def compare_schemas(self, db_schema: dict[str, Any], local_schema: dict[str, Any]) -> list[dict[str, Any]]:
        """Compare database and local schemas."""
        differences = []

        # Compare enums
        db_enums = set(db_schema.get("enums", {}).keys()) - self.system_enums
        local_enums = set(local_schema.get("enums", {}).keys())

        # New enums in database
        for enum_name in db_enums - local_enums:
            differences.append({
                "type": "enum",
                "change": "added",
                "name": enum_name,
                "values": db_schema["enums"][enum_name],
                "severity": "high"
            })

        # Removed enums
        for enum_name in local_enums - db_enums:
            differences.append({
                "type": "enum",
                "change": "removed",
                "name": enum_name,
                "values": local_schema["enums"][enum_name],
                "severity": "high"
            })

        # Modified enums
        for enum_name in db_enums & local_enums:
            db_values = set(db_schema["enums"][enum_name])
            local_values = set(local_schema["enums"][enum_name])
            
            if db_values != local_values:
                added_values = db_values - local_values
                removed_values = local_values - db_values
                
                differences.append({
                    "type": "enum",
                    "change": "modified",
                    "name": enum_name,
                    "added_values": list(added_values),
                    "removed_values": list(removed_values),
                    "severity": "high"
                })

        # Compare tables
        db_tables = set(db_schema.get("tables", {}).keys())
        local_tables = set(local_schema.get("tables", {}).keys())

        # New tables in database
        for table_name in db_tables - local_tables:
            differences.append({
                "type": "table",
                "change": "added",
                "name": table_name,
                "columns": db_schema["tables"][table_name]["columns"],
                "severity": "high"
            })

        # Removed tables
        for table_name in local_tables - db_tables:
            differences.append({
                "type": "table",
                "change": "removed",
                "name": table_name,
                "columns": local_schema["tables"][table_name]["columns"],
                "severity": "high"
            })

        # Modified tables
        for table_name in db_tables & local_tables:
            db_columns = {col["column_name"]: col for col in db_schema["tables"][table_name]["columns"]}
            local_columns = {col["column_name"]: col for col in local_schema["tables"][table_name]["columns"]}
            
            # New columns
            for col_name in db_columns.keys() - local_columns.keys():
                differences.append({
                    "type": "table",
                    "change": "column_added",
                    "table": table_name,
                    "column": col_name,
                    "column_def": db_columns[col_name],
                    "severity": "medium"
                })

            # Removed columns
            for col_name in local_columns.keys() - db_columns.keys():
                differences.append({
                    "type": "table",
                    "change": "column_removed",
                    "table": table_name,
                    "column": col_name,
                    "column_def": local_columns[col_name],
                    "severity": "high"
                })

            # Modified columns
            for col_name in db_columns.keys() & local_columns.keys():
                db_col = db_columns[col_name]
                local_col = local_columns[col_name]
                
                if db_col != local_col:
                    differences.append({
                        "type": "table",
                        "change": "column_modified",
                        "table": table_name,
                        "column": col_name,
                        "old_def": local_col,
                        "new_def": db_col,
                        "severity": "medium"
                    })

        return differences