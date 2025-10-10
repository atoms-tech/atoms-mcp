"""Schema validators - stub for backward compatibility."""

from typing import Any, Dict


class ValidationError(Exception):
    """Validation error exception."""
    pass


def validate_before_create(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate data before creating a record.
    
    Args:
        table: Table name
        data: Data to validate
        
    Returns:
        Validated data
        
    Raises:
        ValidationError: If validation fails
    """
    # Basic validation - just return data for now
    # Real validation logic was moved to pheno_vendor/pydevkit
    return data


def validate_before_update(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate data before updating a record.
    
    Args:
        table: Table name
        data: Data to validate
        
    Returns:
        Validated data
        
    Raises:
        ValidationError: If validation fails
    """
    # Basic validation - just return data for now
    # Real validation logic was moved to pheno_vendor/pydevkit
    return data

