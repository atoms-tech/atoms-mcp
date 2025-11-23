# Docstring Standards for Atoms MCP
## Complete Guide for Code Documentation

---

## 📋 Docstring Format

All docstrings use **Google-style format** for compatibility with Sphinx autodoc.

---

## 🔧 Module Docstring Template

```python
"""Module name: Brief one-line description.

Longer description of what this module does, its purpose,
and how it fits into the system architecture.

This module is responsible for [specific responsibility].
It provides [key functionality].

Key Components:
    - ComponentA: Description of what it does
    - ComponentB: Description of what it does
    - ComponentC: Description of what it does

Architecture:
    The module follows [pattern name] pattern:
    [Brief architecture description]

Dependencies:
    - service_module: For business logic
    - infrastructure_module: For external services

Example:
    Basic usage example:
    
    >>> from module_name import main_function
    >>> result = main_function(param1="value")
    >>> print(result)
    {'success': True, 'data': {...}}

Note:
    Important notes about the module, such as:
    - Thread safety considerations
    - Performance characteristics
    - Known limitations
"""
```

---

## 🎯 Function Docstring Template

```python
def function_name(
    param1: str,
    param2: int,
    param3: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Brief one-line description of what function does.
    
    Longer description explaining:
    - What the function does
    - Why it exists
    - When to use it
    - Any important behavior
    
    This function is responsible for [specific task].
    It handles [specific cases].
    
    Args:
        param1 (str): Description of param1.
            Can be one of: 'value1', 'value2', 'value3'.
            Example: "my_value"
            
        param2 (int): Description of param2.
            Must be positive. Default behavior if not provided.
            Example: 42
            
        param3 (Optional[Dict[str, Any]]): Description of param3.
            If provided, should contain keys: 'key1', 'key2'.
            Default: None (uses default behavior)
            Example: {'key1': 'value1', 'key2': 'value2'}
    
    Returns:
        Dict[str, Any]: Description of return value.
            Structure:
            {
                'success' (bool): Whether operation succeeded,
                'data' (dict): Operation result data,
                'error' (str): Error message if failed,
                'metadata' (dict): Additional metadata
            }
            
    Raises:
        ValueError: If param1 is not one of allowed values.
            Example: ValueError("param1 must be 'value1' or 'value2'")
            
        TypeError: If param2 is not an integer.
            Example: TypeError("param2 must be int, got str")
            
        PermissionError: If user lacks required permissions.
            Example: PermissionError("User lacks permission to perform action")
            
        TimeoutError: If operation takes too long.
            Example: TimeoutError("Operation timed out after 30s")
    
    Note:
        - This function is async and must be awaited
        - It performs database operations (may be slow)
        - It's thread-safe but not process-safe
        - Performance: O(n) where n is number of items
    
    Warning:
        - Do not call this function in a loop (use batch version)
        - This function modifies state (not idempotent)
        - Requires active database connection
    
    Example:
        Basic usage:
        
        >>> result = await function_name(
        ...     param1="value1",
        ...     param2=42,
        ...     param3={'key1': 'value1'}
        ... )
        >>> print(result)
        {
            'success': True,
            'data': {'id': 'ent_123', 'title': 'My Entity'},
            'error': None,
            'metadata': {'created_at': '2025-11-23T10:00:00Z'}
        }
        
        Error handling:
        
        >>> try:
        ...     result = await function_name(param1="invalid")
        ... except ValueError as e:
        ...     print(f"Invalid parameter: {e}")
        Invalid parameter: param1 must be 'value1' or 'value2'
    
    See Also:
        - related_function: For related functionality
        - other_module.function: For alternative approach
    """
```

---

## 🏛️ Class Docstring Template

```python
class ClassName:
    """Brief one-line description of class.
    
    Longer description explaining:
    - What the class represents
    - Its purpose in the system
    - When to use it
    - Key responsibilities
    
    This class is responsible for [specific responsibility].
    It manages [what it manages].
    
    Attributes:
        attr1 (str): Description of attr1.
            Immutable after initialization.
            Example: "my_value"
            
        attr2 (int): Description of attr2.
            Can be modified. Must be positive.
            Example: 42
            
        attr3 (Optional[Dict]): Description of attr3.
            Lazy-loaded on first access.
            Example: {'key': 'value'}
    
    Properties:
        computed_property (str): Description of computed property.
            Computed from attr1 and attr2.
            Example: "my_value_42"
    
    Example:
        Basic usage:
        
        >>> obj = ClassName(attr1="value", attr2=42)
        >>> obj.method1()
        {'result': 'value'}
        >>> obj.attr2 = 100
        >>> obj.computed_property
        'value_100'
    
    Note:
        - This class is thread-safe
        - Instances are immutable after initialization
        - Uses lazy loading for expensive attributes
    
    Warning:
        - Do not subclass this class (final class)
        - Do not modify attr1 after initialization
    """
    
    def __init__(self, attr1: str, attr2: int):
        """Initialize ClassName.
        
        Args:
            attr1 (str): Description of attr1.
            attr2 (int): Description of attr2.
            
        Raises:
            ValueError: If attr1 is empty.
            TypeError: If attr2 is not int.
        """
    
    def method1(self) -> Dict[str, Any]:
        """Brief description of method1.
        
        Longer description of what method does.
        
        Returns:
            Dict[str, Any]: Description of return value.
            
        Raises:
            RuntimeError: If object is in invalid state.
        """
    
    @property
    def computed_property(self) -> str:
        """Brief description of computed property.
        
        Computed from attr1 and attr2.
        
        Returns:
            str: Description of return value.
        """
```

---

## 🔌 Async Function Docstring

```python
async def async_function(param: str) -> Dict[str, Any]:
    """Brief description of async function.
    
    This is an async function that must be awaited.
    It performs I/O operations (database, network, etc.).
    
    Args:
        param (str): Description of param.
    
    Returns:
        Dict[str, Any]: Description of return value.
    
    Raises:
        asyncio.TimeoutError: If operation times out.
        ConnectionError: If connection fails.
    
    Note:
        - Must be awaited: result = await async_function(...)
        - Performs database operations
        - May take several seconds
        - Cancellable via asyncio.CancelledError
    
    Example:
        >>> result = await async_function("value")
        >>> print(result)
        {'success': True, 'data': {...}}
    """
```

---

## 🛠️ Tool Function Docstring

```python
async def entity_operation(
    operation: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Perform CRUD operations on entities.
    
    This is an MCP tool that agents use to create, read, update,
    delete, and list entities in the Atoms workspace.
    
    Tool Operations:
        - 'create': Create new entity
        - 'read': Read entity by ID
        - 'update': Update entity
        - 'delete': Delete entity
        - 'list': List entities with filters
        - 'search': Search entities by properties
    
    Args:
        operation (str): Operation to perform.
            One of: 'create', 'read', 'update', 'delete', 'list', 'search'
            Example: "create"
            
        entity_type (str): Type of entity.
            One of: 'document', 'requirement', 'task'
            Example: "document"
            
        entity_id (Optional[str]): Entity ID.
            Required for: 'read', 'update', 'delete'
            Optional for: 'create', 'list', 'search'
            Example: "ent_123"
            
        properties (Optional[Dict[str, Any]]): Entity properties.
            Required for: 'create', 'update'
            Optional for: 'list', 'search'
            Example: {'title': 'My Doc', 'content': '...'}
    
    Returns:
        Dict[str, Any]: Tool response.
            {
                'success' (bool): Whether operation succeeded,
                'data' (dict): Entity data or list of entities,
                'error' (str): Error message if failed
            }
    
    Raises:
        ValueError: If operation is invalid.
        AuthenticationError: If authentication fails.
        PermissionError: If user lacks permission.
    
    Agent Reasoning:
        Agents use this tool to:
        1. Create entities for storing information
        2. Read entities to retrieve information
        3. Update entities to modify information
        4. Delete entities to remove information
        5. List entities to discover available entities
        6. Search entities to find specific entities
    
    Example:
        Create entity:
        
        >>> result = await entity_operation(
        ...     operation='create',
        ...     entity_type='document',
        ...     properties={'title': 'My Doc'}
        ... )
        >>> print(result)
        {'success': True, 'data': {'id': 'ent_123'}}
        
        Read entity:
        
        >>> result = await entity_operation(
        ...     operation='read',
        ...     entity_type='document',
        ...     entity_id='ent_123'
        ... )
        >>> print(result)
        {'success': True, 'data': {'id': 'ent_123', 'title': 'My Doc'}}
    """
```

---

## 📝 Inline Comments

Use inline comments for complex logic:

```python
def complex_function(data: List[Dict]) -> List[Dict]:
    """Process data with complex logic.
    
    Args:
        data: List of dictionaries to process.
    
    Returns:
        List of processed dictionaries.
    """
    # Filter out invalid entries (missing required fields)
    valid_data = [
        item for item in data
        if 'id' in item and 'name' in item
    ]
    
    # Sort by name, then by ID (stable sort)
    sorted_data = sorted(
        valid_data,
        key=lambda x: (x['name'], x['id'])
    )
    
    # Enrich each item with computed fields
    enriched_data = []
    for item in sorted_data:
        # Compute full_name from first and last name
        full_name = f"{item.get('first_name', '')} {item.get('last_name', '')}"
        
        enriched_data.append({
            **item,
            'full_name': full_name.strip(),
            'processed_at': datetime.now().isoformat()
        })
    
    return enriched_data
```

---

## ✅ Docstring Checklist

For every function/class:
- [ ] One-line summary
- [ ] Longer description
- [ ] All parameters documented
- [ ] All return values documented
- [ ] All exceptions documented
- [ ] At least one example
- [ ] Related functions/classes linked
- [ ] Important notes/warnings included
- [ ] Type hints included
- [ ] Async functions marked as async

---

## 🔍 Validation

```bash
# Check docstring coverage
python cli.py lint check

# Generate API reference
sphinx-apidoc -o docs/api .

# Validate docstring format
python -m pydocstyle .
```


