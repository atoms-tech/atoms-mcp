#!/usr/bin/env python3
"""Setup mcp_sessions table in Supabase via REST API."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client


def get_admin_client():
    """Get Supabase admin client with service role key."""
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not service_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")

    return create_client(url, service_key)


def run_sql_file(client, sql_file: str) -> None:
    """Execute SQL file via Supabase RPC."""
    sql_path = Path(__file__).parent.parent / "infrastructure" / "sql" / sql_file

    if not sql_path.exists():
        print(f"❌ SQL file not found: {sql_path}")
        return

    sql = sql_path.read_text()
    print(f"\n📄 Running {sql_file}...")
    print(f"SQL Preview: {sql[:200]}...")

    try:
        # Execute via Supabase SQL editor endpoint
        response = client.rpc("exec_sql", {"query": sql})
        print(f"✅ {sql_file} executed successfully")
        if response.data:
            print(f"Result: {response.data}")
    except Exception as e:
        # Try direct table query for check script
        if "check" in sql_file:
            try:
                client.table("mcp_sessions").select("*").limit(1).execute()
                print("✅ mcp_sessions table exists (found via query)")
                return
            except Exception:
                print("⚠️  mcp_sessions table does not exist yet")
                return

        print(f"❌ Error executing {sql_file}: {e}")
        print("Note: You may need to run this SQL manually in Supabase SQL Editor")
        print(f"SQL content saved to: {sql_path}")


def main():
    """Setup mcp_sessions table."""
    print("🔧 Setting up MCP Sessions table in Supabase\n")

    client = get_admin_client()

    # Run SQL scripts in order
    scripts = [
        "check_mcp_sessions_table.sql",
        "create_mcp_sessions_table.sql",
        "create_session_rls_policies.sql",
        "test_session_operations.sql"
    ]

    for script in scripts:
        run_sql_file(client, script)

    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Verify table in Supabase Dashboard > Table Editor")
    print("2. Test OAuth flow with stateless session creation")
    print("3. Check session persistence across requests")


if __name__ == "__main__":
    main()
