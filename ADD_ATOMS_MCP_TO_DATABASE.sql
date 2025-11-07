-- Add Atoms MCP servers to database
-- Run this in Supabase SQL Editor

-- Add production Atoms MCP
INSERT INTO mcp_servers (
    name,
    url,
    transport_type,
    scope,
    is_internal,
    enabled,
    created_at,
    updated_at
) VALUES (
    'atoms-mcp',
    'https://mcp.atoms.tech/api/mcp',
    'http',
    'system',
    true,
    true,
    NOW(),
    NOW()
) ON CONFLICT (name) DO UPDATE SET
    is_internal = true,
    url = 'https://mcp.atoms.tech/api/mcp',
    enabled = true,
    updated_at = NOW();

-- Add dev Atoms MCP (optional)
INSERT INTO mcp_servers (
    name,
    url,
    transport_type,
    scope,
    is_internal,
    enabled,
    created_at,
    updated_at
) VALUES (
    'atoms-mcp-dev',
    'https://mcpdev.atoms.tech/api/mcp',
    'http',
    'system',
    true,
    true,
    NOW(),
    NOW()
) ON CONFLICT (name) DO UPDATE SET
    is_internal = true,
    url = 'https://mcpdev.atoms.tech/api/mcp',
    enabled = true,
    updated_at = NOW();

-- Verify the insertion
SELECT name, url, transport_type, scope, is_internal, enabled 
FROM mcp_servers 
WHERE name IN ('atoms-mcp', 'atoms-mcp-dev');

