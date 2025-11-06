#!/usr/bin/env python3
"""Generate Pydantic models from Supabase schema (Simple approach).

This script queries the Supabase information_schema to generate Pydantic models.
Works without supabase-pydantic dependency.

Usage:
    python scripts/generate_schemas_simple.py
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def get_python_type(pg_type: str, is_nullable: bool) -> str:
    """Convert PostgreSQL type to Python type annotation."""
    type_map = {
        "uuid": "UUID",
        "text": "str",
        "character varying": "str",
        "varchar": "str",
        "integer": "int",
        "bigint": "int",
        "smallint": "int",
        "boolean": "bool",
        "timestamp with time zone": "datetime",
        "timestamp without time zone": "datetime",
        "timestamptz": "datetime",
        "date": "datetime",
        "jsonb": "Dict[str, Any]",
        "json": "Dict[str, Any]",
        "numeric": "float",
        "real": "float",
        "double precision": "float",
        "USER-DEFINED": "str",  # Enums
    }
    
    python_type = type_map.get(pg_type, "Any")
    
    if is_nullable:
        return f"Optional[{python_type}]"
    return python_type

def fetch_table_schema(supabase_url: str, supabase_key: str, table_name: str) -> List[Dict[str, Any]]:
    """Fetch table schema from Supabase."""
    from supabase import create_client
    
    client = create_client(supabase_url, supabase_key)
    
    # Query information_schema
    query = f"""
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default,
        udt_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = '{table_name}'
    ORDER BY ordinal_position;
    """
    
    result = client.rpc('exec_sql', {'query': query}).execute()
    return result.data if result.data else []

def generate_model_code(table_name: str, columns: List[Dict[str, Any]]) -> str:
    """Generate Pydantic model code for a table."""
    class_name = ''.join(word.capitalize() for word in table_name.split('_'))
    
    lines = [
        f"class {class_name}(BaseModel):",
        f'    """Model for {table_name} table."""',
        ""
    ]
    
    for col in columns:
        col_name = col['column_name']
        data_type = col['data_type']
        is_nullable = col['is_nullable'] == 'YES'
        has_default = col['column_default'] is not None
        
        python_type = get_python_type(data_type, is_nullable)
        
        # Add field with default if nullable or has default
        if is_nullable or has_default:
            lines.append(f"    {col_name}: {python_type} = None")
        else:
            lines.append(f"    {col_name}: {python_type}")
    
    lines.extend([
        "",
        "    class Config:",
        "        from_attributes = True",
        ""
    ])
    
    return "\n".join(lines)

def main():
    """Generate Pydantic models from Supabase."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        sys.exit(1)
    
    print(f"🔍 Connecting to Supabase: {supabase_url}")
    
    # Tables to generate
    tables = [
        "organizations",
        "projects",
        "documents",
        "requirements",
        "test_req",
        "blocks",
        "properties",
        "trace_links",
        "assignments",
        "profiles",
        "organization_members",
        "project_members",
        "organization_invitations",
        "requirement_tests",
        "audit_logs",
        "notifications",
        "external_documents",
        "test_matrix_views",
        "mcp_sessions",
    ]
    
    # Create output directory
    output_dir = Path("schemas/generated")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Generating models for {len(tables)} tables...")
    
    # Generate models
    models_code = []
    model_names = []
    
    for table in tables:
        try:
            print(f"  ⏳ Fetching schema for {table}...")
            columns = fetch_table_schema(supabase_url, supabase_key, table)
            
            if not columns:
                print(f"  ⚠️  Warning: No columns found for {table}")
                continue
            
            model_code = generate_model_code(table, columns)
            class_name = ''.join(word.capitalize() for word in table.split('_'))
            
            models_code.append(model_code)
            model_names.append(class_name)
            
            print(f"  ✅ Generated {class_name}")
            
        except Exception as e:
            print(f"  ⚠️  Warning: Failed to generate {table}: {e}")
            continue
    
    # Write models file
    output_file = output_dir / "models.py"
    
    with open(output_file, "w") as f:
        f.write('"""Auto-generated Pydantic models from Supabase schema.\n\n')
        f.write('DO NOT EDIT THIS FILE MANUALLY!\n')
        f.write('Generated by: scripts/generate_schemas_simple.py\n')
        f.write('"""\n\n')
        f.write('from datetime import datetime\n')
        f.write('from typing import Any, Dict, Optional\n')
        f.write('from uuid import UUID\n')
        f.write('from pydantic import BaseModel\n\n\n')
        
        f.write('\n\n'.join(models_code))
    
    # Write __init__.py
    init_file = output_dir / "__init__.py"
    with open(init_file, "w") as f:
        f.write('"""Auto-generated Pydantic models from Supabase."""\n\n')
        f.write('from .models import (\n')
        for name in model_names:
            f.write(f'    {name},\n')
        f.write(')\n\n')
        f.write('__all__ = [\n')
        for name in model_names:
            f.write(f'    "{name}",\n')
        f.write(']\n')
    
    print(f"\n✅ Successfully generated {len(model_names)} models")
    print(f"📄 Output: {output_file}")
    print(f"📄 Exports: {init_file}")
    print("\n🎉 Schema generation complete!")

if __name__ == "__main__":
    main()

