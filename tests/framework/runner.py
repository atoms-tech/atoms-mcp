"""
Atoms MCP Test Runner

Extends pheno-sdk's BaseTestRunner with Atoms-specific configuration.

This is the slimmed-down version (~30 lines vs ~672 before) that leverages
all shared test execution infrastructure from pheno-sdk.
"""

from typing import Any, Dict, List
from mcp_qa.core.base import BaseTestRunner


class AtomsTestRunner(BaseTestRunner):
    """
    Atoms-specific test runner.
    
    Extends BaseTestRunner with Atoms-specific:
    - Metadata for reports
    - Test category ordering
    - Any Atoms-specific execution customizations
    """
    
    def _get_metadata(self) -> Dict[str, Any]:
        """
        Get Atoms-specific metadata for test reports.
        
        Returns:
            Dict with Atoms metadata
        """
        return {
            "endpoint": getattr(self.client_adapter, 'endpoint', 'unknown'),
            "project": "atoms",
            "environment": "production",
            "adapter_type": "AtomsMCPClientAdapter"
        }
    
    def _get_category_order(self) -> List[str]:
        """
        Get Atoms test category execution order.
        
        Returns:
            List of categories in preferred execution order
        """
        return ["core", "entity", "query", "relationship", "workflow", "integration"]


__all__ = ["AtomsTestRunner"]
