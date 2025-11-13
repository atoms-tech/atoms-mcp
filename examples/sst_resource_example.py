"""
Example: Using SST Resources in Python

This example shows how to access SST-linked resources in your Python code.
"""

from __future__ import annotations
import os


def example_using_sst_sdk():
    """
    Example using the SST Python SDK to access linked resources.
    
    This is the recommended approach when using SST.
    """
    try:
        from sst import Resource
        
        # Access secrets that were linked in sst.config.ts
        supabase_url = Resource.SupabaseUrl.value
        supabase_key = Resource.SupabaseKey.value
        workos_api_key = Resource.WorkosApiKey.value
        
        print(f"Supabase URL: {supabase_url}")
        print(f"Supabase Key: {supabase_key[:10]}...")
        print(f"WorkOS API Key: {workos_api_key[:10]}...")
        
        # You can also access function properties
        # (though you typically wouldn't need your own function's ARN)
        # function_arn = Resource.AtomsMcpServer.arn
        
        return {
            "supabase_url": supabase_url,
            "supabase_key": supabase_key,
            "workos_api_key": workos_api_key,
        }
        
    except ImportError:
        print("SST SDK not available - falling back to environment variables")
        return example_using_env_vars()


def example_using_env_vars():
    """
    Fallback: Using environment variables directly.
    
    This works both with SST and other deployment methods (like Vercel).
    SST automatically sets environment variables for linked resources.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    workos_api_key = os.getenv("WORKOS_API_KEY")
    
    return {
        "supabase_url": supabase_url,
        "supabase_key": supabase_key,
        "workos_api_key": workos_api_key,
    }


def example_hybrid_approach():
    """
    Hybrid approach: Try SST SDK first, fall back to env vars.
    
    This is the most flexible approach that works in all environments.
    """
    try:
        from sst import Resource
        
        # Try to get from SST Resource first
        config = {
            "supabase_url": Resource.SupabaseUrl.value,
            "supabase_key": Resource.SupabaseKey.value,
            "workos_api_key": Resource.WorkosApiKey.value,
        }
        print("✅ Using SST Resources")
        return config
        
    except (ImportError, AttributeError):
        # Fall back to environment variables
        config = {
            "supabase_url": os.getenv("SUPABASE_URL"),
            "supabase_key": os.getenv("SUPABASE_KEY"),
            "workos_api_key": os.getenv("WORKOS_API_KEY"),
        }
        print("⚠️  SST not available, using environment variables")
        return config


# Example usage in your actual code
def get_supabase_client():
    """
    Example: Creating a Supabase client using SST resources.
    """
    try:
        from sst import Resource
        from supabase import create_client
        
        client = create_client(
            Resource.SupabaseUrl.value,
            Resource.SupabaseKey.value
        )
        return client
        
    except ImportError:
        # Fallback for non-SST environments
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        
        client = create_client(url, key)
        return client


if __name__ == "__main__":
    print("=== SST Resource Examples ===\n")
    
    print("1. Using SST SDK:")
    result1 = example_using_sst_sdk()
    print(f"   Result: {result1}\n")
    
    print("2. Using Environment Variables:")
    result2 = example_using_env_vars()
    print(f"   Result: {result2}\n")
    
    print("3. Hybrid Approach (Recommended):")
    result3 = example_hybrid_approach()
    print(f"   Result: {result3}\n")

