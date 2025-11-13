/// <reference path="./.sst/platform/config.d.ts" />

/**
 * SST Configuration for Atoms MCP Server
 * 
 * This configuration deploys the Python FastMCP server to AWS Lambda
 * with proper environment variables and permissions.
 */

export default $config({
  app(input) {
    return {
      name: "atoms-mcp",
      removal: input?.stage === "production" ? "retain" : "remove",
      home: "aws",
      providers: {
        aws: {
          region: "us-east-1", // Change to your preferred region
        },
      },
    };
  },
  async run() {
    // Create secrets for sensitive environment variables
    const supabaseUrl = new sst.Secret("SupabaseUrl");
    const supabaseKey = new sst.Secret("SupabaseKey");
    const workosApiKey = new sst.Secret("WorkosApiKey");
    const workosClientId = new sst.Secret("WorkosClientId");
    const workosRedirectUri = new sst.Secret("WorkosRedirectUri");

    // Deploy the FastMCP server as a Lambda function
    const mcpFunction = new sst.aws.Function("AtomsMcpServer", {
      runtime: "python3.12",
      handler: "lambda_handler.handler",
      timeout: "30 seconds",
      memory: "1024 MB",
      
      // Link secrets to the function
      link: [
        supabaseUrl,
        supabaseKey,
        workosApiKey,
        workosClientId,
        workosRedirectUri,
      ],
      
      // Environment variables
      environment: {
        ATOMS_FASTMCP_TRANSPORT: "http",
        ATOMS_FASTMCP_HTTP_PATH: "/api/mcp",
        PYTHONPATH: "/var/task",
      },
      
      // Enable function URL for HTTP access
      url: {
        cors: {
          allowOrigins: ["*"],
          allowMethods: ["GET", "POST", "OPTIONS"],
          allowHeaders: ["*"],
          allowCredentials: true,
        },
      },
      
      // Python-specific configuration
      python: {
        // Set to true if you need container deployment (for packages >250MB)
        container: false,
      },
    });

    // Output the function URL
    return {
      functionUrl: mcpFunction.url,
      functionArn: mcpFunction.arn,
    };
  },
});

