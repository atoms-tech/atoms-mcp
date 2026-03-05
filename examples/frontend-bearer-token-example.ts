/**
 * Frontend Bearer Token Authentication Example
 * 
 * This example demonstrates how to authenticate with the Atoms MCP server
 * using AuthKit JWT tokens passed via the Authorization header.
 * 
 * This approach allows your frontend to use the same AuthKit authentication
 * for both Supabase and MCP server access.
 */

import { createClient } from '@supabase/supabase-js';
import { createClient as createAuthKitClient } from '@workos-inc/authkit-js';

// Configuration
const MCP_ENDPOINT = process.env.NEXT_PUBLIC_MCP_ENDPOINT || 'https://mcp.atoms.tech/api/mcp';
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const WORKOS_CLIENT_ID = process.env.NEXT_PUBLIC_WORKOS_CLIENT_ID!;
const WORKOS_AUTH_DOMAIN = process.env.NEXT_PUBLIC_WORKOS_AUTH_DOMAIN!;

/**
 * Initialize AuthKit client
 */
const authkit = await createAuthKitClient(WORKOS_CLIENT_ID, {
  apiHostname: WORKOS_AUTH_DOMAIN,
});

/**
 * Initialize Supabase client with AuthKit token
 */
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  accessToken: async () => {
    return await authkit.getAccessToken();
  },
});

/**
 * MCP Client class for making authenticated requests
 */
class MCPClient {
  private endpoint: string;
  private requestId: number = 0;

  constructor(endpoint: string) {
    this.endpoint = endpoint;
  }

  /**
   * Call an MCP tool with bearer token authentication
   */
  async callTool<T = any>(
    toolName: string,
    args: Record<string, any>
  ): Promise<T> {
    // Get fresh access token from AuthKit
    const accessToken = await authkit.getAccessToken();

    if (!accessToken) {
      throw new Error('Not authenticated - please sign in');
    }

    // Make JSON-RPC 2.0 request with Bearer token
    const response = await fetch(this.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: ++this.requestId,
        method: 'tools/call',
        params: {
          name: toolName,
          arguments: args,
        },
      }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication failed - token may be expired');
      }
      throw new Error(`MCP request failed: ${response.statusText}`);
    }

    const result = await response.json();

    if (result.error) {
      throw new Error(`MCP error: ${result.error.message}`);
    }

    return result.result;
  }

  /**
   * Create an entity
   */
  async createEntity(
    entityType: string,
    data: Record<string, any>
  ): Promise<any> {
    return this.callTool('entity_tool', {
      entity_type: entityType,
      operation: 'create',
      data,
    });
  }

  /**
   * Read an entity
   */
  async readEntity(
    entityType: string,
    entityId: string,
    includeRelations: boolean = false
  ): Promise<any> {
    return this.callTool('entity_tool', {
      entity_type: entityType,
      operation: 'read',
      entity_id: entityId,
      include_relations: includeRelations,
    });
  }

  /**
   * Update an entity
   */
  async updateEntity(
    entityType: string,
    entityId: string,
    data: Record<string, any>
  ): Promise<any> {
    return this.callTool('entity_tool', {
      entity_type: entityType,
      operation: 'update',
      entity_id: entityId,
      data,
    });
  }

  /**
   * Delete an entity
   */
  async deleteEntity(
    entityType: string,
    entityId: string,
    softDelete: boolean = true
  ): Promise<any> {
    return this.callTool('entity_tool', {
      entity_type: entityType,
      operation: 'delete',
      entity_id: entityId,
      soft_delete: softDelete,
    });
  }

  /**
   * List entities with filters
   */
  async listEntities(
    entityType: string,
    filters?: Record<string, any>,
    limit: number = 100,
    offset: number = 0
  ): Promise<any> {
    return this.callTool('entity_tool', {
      entity_type: entityType,
      operation: 'list',
      filters,
      limit,
      offset,
    });
  }

  /**
   * Get workspace context
   */
  async getWorkspaceContext(): Promise<any> {
    return this.callTool('workspace_tool', {
      operation: 'get_context',
    });
  }

  /**
   * Set workspace context
   */
  async setWorkspaceContext(
    contextType: string,
    entityId: string,
    organizationId?: string,
    projectId?: string
  ): Promise<any> {
    return this.callTool('workspace_tool', {
      operation: 'set_context',
      context_type: contextType,
      entity_id: entityId,
      organization_id: organizationId,
      project_id: projectId,
    });
  }

  /**
   * Execute a workflow
   */
  async executeWorkflow(
    workflow: string,
    parameters: Record<string, any>
  ): Promise<any> {
    return this.callTool('workflow_tool', {
      workflow,
      parameters,
    });
  }

  /**
   * Query data with RAG search
   */
  async queryData(
    operation: string,
    params: Record<string, any>
  ): Promise<any> {
    return this.callTool('query_tool', {
      operation,
      ...params,
    });
  }
}

// Create MCP client instance
const mcpClient = new MCPClient(MCP_ENDPOINT);

/**
 * Example usage in a React component
 */
export function useAtomsMCP() {
  const createProject = async (name: string, description: string) => {
    try {
      const result = await mcpClient.createEntity('project', {
        name,
        description,
        status: 'active',
      });
      return result;
    } catch (error) {
      console.error('Failed to create project:', error);
      throw error;
    }
  };

  const getProjects = async () => {
    try {
      const result = await mcpClient.listEntities('project', {
        status: 'active',
      });
      return result.data || [];
    } catch (error) {
      console.error('Failed to get projects:', error);
      throw error;
    }
  };

  const updateProject = async (
    projectId: string,
    updates: Record<string, any>
  ) => {
    try {
      const result = await mcpClient.updateEntity('project', projectId, updates);
      return result;
    } catch (error) {
      console.error('Failed to update project:', error);
      throw error;
    }
  };

  const deleteProject = async (projectId: string) => {
    try {
      const result = await mcpClient.deleteEntity('project', projectId);
      return result;
    } catch (error) {
      console.error('Failed to delete project:', error);
      throw error;
    }
  };

  const getCurrentContext = async () => {
    try {
      const result = await mcpClient.getWorkspaceContext();
      return result;
    } catch (error) {
      console.error('Failed to get workspace context:', error);
      throw error;
    }
  };

  return {
    createProject,
    getProjects,
    updateProject,
    deleteProject,
    getCurrentContext,
    // Expose raw client for advanced usage
    client: mcpClient,
  };
}

/**
 * Example: Direct usage without React
 */
async function exampleUsage() {
  try {
    // Create a new project
    const project = await mcpClient.createEntity('project', {
      name: 'My New Project',
      description: 'A project created via MCP',
      status: 'active',
    });
    console.log('Created project:', project);

    // Get workspace context
    const context = await mcpClient.getWorkspaceContext();
    console.log('Current context:', context);

    // List all active projects
    const projects = await mcpClient.listEntities('project', {
      status: 'active',
    });
    console.log('Active projects:', projects);

    // Execute a workflow
    const workflowResult = await mcpClient.executeWorkflow('setup_project', {
      name: 'Workflow Project',
      organization_id: 'org_123',
    });
    console.log('Workflow result:', workflowResult);

    // Query with RAG search
    const searchResults = await mcpClient.queryData('rag_search', {
      query: 'authentication documentation',
      entity_type: 'document',
      limit: 10,
    });
    console.log('Search results:', searchResults);
  } catch (error) {
    console.error('Error:', error);
  }
}

// Export for use in other modules
export { mcpClient, MCPClient };
export default mcpClient;

