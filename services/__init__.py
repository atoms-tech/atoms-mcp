"""Services Module: Business Logic Layer for Atoms MCP Server.

This module provides the business logic layer for the Atoms MCP Server. Services
implement domain logic, validation rules, and orchestration of infrastructure
adapters. Services are called by tools and do not directly access external
services (that's the responsibility of infrastructure adapters).

Architecture:
    The services layer follows clean architecture principles:
    - Tools call services (not infrastructure directly)
    - Services implement business logic
    - Services call infrastructure adapters
    - Services are testable and independent
    - Services handle validation and error handling

Services Provided:
    - EntityService: Entity CRUD and search operations
    - RelationshipService: Relationship management
    - WorkflowService: Workflow execution and orchestration
    - QueryService: Data querying and search
    - WorkspaceService: Workspace context management

Key Responsibilities:
    1. Business Logic: Implement domain rules and workflows
    2. Validation: Validate inputs and enforce constraints
    3. Orchestration: Coordinate multiple infrastructure calls
    4. Error Handling: Handle errors gracefully
    5. Logging: Log important operations for debugging

Design Principles:
    - Single Responsibility: Each service has one reason to change
    - Dependency Injection: Services receive dependencies
    - Testability: Services are easy to test
    - Reusability: Services can be used by multiple tools
    - Consistency: Services follow common patterns

Example:
    Using services in tools:

    >>> from services.entity_service import EntityService
    >>> service = EntityService(db_adapter, cache_adapter)
    >>> entity = await service.create_entity(
    ...     entity_type='document',
    ...     properties={'title': 'My Doc'}
    ... )
    >>> print(entity)
    {'id': 'ent_123', 'title': 'My Doc', 'created_at': '2025-11-23T...'}

Note:
    - All services are async
    - Services use dependency injection
    - Services handle validation
    - Services log operations
    - Services are independent of HTTP/MCP

See Also:
    - infrastructure/: Adapter implementations
    - tools/: Tool implementations that use services
    - auth/: Authentication and session management
"""

__all__ = ["auth"]

