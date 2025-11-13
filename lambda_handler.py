"""
AWS Lambda handler for Atoms MCP Server.

This module provides a Lambda-compatible handler that wraps the FastMCP ASGI application
using Mangum for AWS Lambda integration.
"""

from __future__ import annotations
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure proper Python path for Lambda
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if '/var/task' not in sys.path and os.path.exists('/var/task'):
    sys.path.insert(0, '/var/task')

try:
    # Import the ASGI app from app.py
    from app import app as asgi_app
    
    # Use Mangum to wrap the ASGI app for Lambda
    from mangum import Mangum
    
    # Create the Lambda handler
    handler = Mangum(asgi_app, lifespan="off")
    
    logger.info("✅ Lambda handler initialized successfully")
    
except ImportError as e:
    logger.error(f"❌ Failed to import required modules: {e}")
    logger.error("Make sure 'mangum' is installed in your dependencies")
    
    # Fallback handler for errors
    def handler(event, context):
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": '{"error": "Server initialization failed", "details": "Missing required dependencies"}',
        }

except Exception as init_error:
    logger.error(f"❌ Unexpected error during initialization: {init_error}")
    import traceback
    traceback.print_exc()
    
    # Fallback handler for errors
    error_message = str(init_error)
    def handler(event, context):
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": f'{{"error": "Server initialization failed", "details": "{error_message}"}}',
        }


# Export handler for Lambda
__all__ = ["handler"]

