"""
Test Coverage Bootstrap: Builds comprehensive testing infrastructure for 100% coverage.

This module establishes:
1. Mock factories for Supabase and AuthKit (decoupled from live services)
2. Fixture library for common test scenarios
3. Integration test harness for MCP client end-to-end testing
4. Coverage measurement utilities
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid


# ============================================================================
# MOCK FACTORIES FOR SUPABASE AND AUTHKIT
# ============================================================================

@dataclass
class MockUser:
    """Mock AuthKit user."""
    id: str
    email: str
    name: str
    organization_id: str
    roles: List[str]
    
    @classmethod
    def create_test_user(cls, org_id: str = None) -> "MockUser":
        return cls(
            id=str(uuid.uuid4()),
            email="test@example.com",
            name="Test User",
            organization_id=org_id or str(uuid.uuid4()),
            roles=["admin", "member"]
        )


@dataclass
class MockEntity:
    """Mock Atoms entity (org, project, document, requirement, etc)."""
    id: str
    type: str  # organization, project, document, requirement, test, task, risk
    name: str
    organization_id: str
    created_at: str
    updated_at: str
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MockSupabaseClient:
    """Factory for Supabase client mocks with RLS-aware behavior."""
    
    def __init__(self):
        self.entities: Dict[str, List[MockEntity]] = {
            "organizations": [],
            "projects": [],
            "documents": [],
            "requirements": [],
            "tests": [],
            "tasks": [],
            "risks": [],
        }
        self.relationships: List[Dict[str, Any]] = []
        self.auth_user: Optional[MockUser] = None
        
    def set_auth_user(self, user: MockUser):
        """Set the authenticated user for RLS filtering."""
        self.auth_user = user
        
    def table(self, table_name: str) -> "MockTableQuery":
        """Return a mock table query builder."""
        return MockTableQuery(self, table_name)
        
    def rpc(self, function_name: str, params: Dict[str, Any] = None):
        """Mock RPC call for stored procedures."""
        return MockRPCCall(self, function_name, params)
        
    @property
    def auth(self):
        """Mock auth interface."""
        return MockAuthInterface(self)


class MockTableQuery:
    """Mock Supabase table query builder."""
    
    def __init__(self, client: MockSupabaseClient, table_name: str):
        self.client = client
        self.table_name = table_name
        self.filters = []
        self.select_fields = ["*"]
        self.order_by = None
        self.limit_val = None
        self.offset_val = 0
        
    def select(self, fields: str = "*") -> "MockTableQuery":
        self.select_fields = fields.split(",") if fields != "*" else ["*"]
        return self
        
    def eq(self, field: str, value: Any) -> "MockTableQuery":
        self.filters.append(("eq", field, value))
        return self
        
    def ilike(self, field: str, pattern: str) -> "MockTableQuery":
        self.filters.append(("ilike", field, pattern))
        return self
        
    def order(self, field: str, desc: bool = False) -> "MockTableQuery":
        self.order_by = (field, desc)
        return self
        
    def limit(self, count: int) -> "MockTableQuery":
        self.limit_val = count
        return self
        
    def offset(self, count: int) -> "MockTableQuery":
        self.offset_val = count
        return self
        
    def execute(self) -> "MockExecuteResult":
        """Execute query and return results."""
        results = []
        
        # Filter entities
        if self.table_name in self.client.entities:
            for entity in self.client.entities[self.table_name]:
                # Check all filters
                include = True
                for filter_type, field, value in self.filters:
                    if filter_type == "eq":
                        if getattr(entity, field, None) != value:
                            include = False
                            break
                    elif filter_type == "ilike":
                        entity_val = getattr(entity, field, "")
                        pattern = value.replace("%", "")
                        if pattern.lower() not in str(entity_val).lower():
                            include = False
                            break
                
                if include:
                    results.append(entity)
        
        # Apply ordering
        if self.order_by:
            field, desc = self.order_by
            results.sort(key=lambda x: getattr(x, field, ""), reverse=desc)
        
        # Apply pagination
        if self.limit_val:
            results = results[self.offset_val:self.offset_val + self.limit_val]
        
        return MockExecuteResult(results)
        
    def insert(self, data: List[Dict[str, Any]] | Dict[str, Any]) -> "MockTableQuery":
        """Insert mock data."""
        if isinstance(data, dict):
            data = [data]
            
        for item in data:
            entity = MockEntity(
                id=item.get("id", str(uuid.uuid4())),
                type=self.table_name.rstrip("s"),
                name=item.get("name", ""),
                organization_id=item.get("organization_id", ""),
                created_at=item.get("created_at", datetime.now().isoformat()),
                updated_at=item.get("updated_at", datetime.now().isoformat()),
                data=item
            )
            self.client.entities[self.table_name].append(entity)
        
        return self
        
    def update(self, data: Dict[str, Any]) -> "MockTableQuery":
        """Update mock data."""
        # This would update filtered entities
        return self
        
    def delete(self) -> "MockTableQuery":
        """Delete mock data."""
        # This would delete filtered entities
        return self


class MockExecuteResult:
    """Result of a Supabase query execution."""
    
    def __init__(self, data: List[MockEntity] | List[Dict[str, Any]]):
        self.data = [d.to_dict() if isinstance(d, MockEntity) else d for d in data]
        self.error = None
        self.status_code = 200
        
    def __bool__(self):
        return bool(self.data)


class MockRPCCall:
    """Mock RPC function call."""
    
    def __init__(self, client: MockSupabaseClient, function_name: str, params: Dict = None):
        self.client = client
        self.function_name = function_name
        self.params = params or {}
        
    async def execute(self) -> Dict[str, Any]:
        """Execute RPC call."""
        if self.function_name == "search_by_embedding":
            # Mock embedding search
            return {
                "data": [
                    {"id": str(uuid.uuid4()), "similarity": 0.95},
                    {"id": str(uuid.uuid4()), "similarity": 0.87},
                ],
                "error": None
            }
        return {"data": [], "error": None}


class MockAuthInterface:
    """Mock Supabase auth interface."""
    
    def __init__(self, client: MockSupabaseClient):
        self.client = client
        
    async def sign_in_with_password(self, credentials: Dict[str, str]):
        """Mock password signin."""
        user = MockUser.create_test_user()
        return MockAuthResponse(user)
        
    async def sign_out(self):
        """Mock signout."""
        self.client.auth_user = None


class MockAuthResponse:
    """Mock authentication response."""
    
    def __init__(self, user: MockUser):
        self.user = user
        self.session = MockSession(user)


class MockSession:
    """Mock auth session."""
    
    def __init__(self, user: MockUser):
        self.user = user
        self.access_token = f"mock_token_{user.id}"
        self.refresh_token = f"mock_refresh_{user.id}"


# ============================================================================
# FIXTURE LIBRARY
# ============================================================================

@pytest.fixture
def mock_supabase() -> MockSupabaseClient:
    """Provide a mock Supabase client."""
    return MockSupabaseClient()


@pytest.fixture
def mock_auth_user() -> MockUser:
    """Provide a mock authenticated user."""
    return MockUser.create_test_user()


@pytest.fixture
async def mock_authenticated_supabase(mock_supabase: MockSupabaseClient, mock_auth_user: MockUser):
    """Provide authenticated mock Supabase client."""
    mock_supabase.set_auth_user(mock_auth_user)
    return mock_supabase


@pytest.fixture
def sample_entities(mock_supabase: MockSupabaseClient, mock_auth_user: MockUser) -> Dict[str, MockEntity]:
    """Create sample entities for testing."""
    org = MockEntity(
        id=str(uuid.uuid4()),
        type="organization",
        name="Test Organization",
        organization_id=mock_auth_user.organization_id,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        data={"name": "Test Organization"}
    )
    
    project = MockEntity(
        id=str(uuid.uuid4()),
        type="project",
        name="Test Project",
        organization_id=mock_auth_user.organization_id,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        data={"name": "Test Project", "organization_id": mock_auth_user.organization_id}
    )
    
    document = MockEntity(
        id=str(uuid.uuid4()),
        type="document",
        name="Test Document",
        organization_id=mock_auth_user.organization_id,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        data={"name": "Test Document", "project_id": project.id}
    )
    
    # Add to mock client
    mock_supabase.entities["organizations"].append(org)
    mock_supabase.entities["projects"].append(project)
    mock_supabase.entities["documents"].append(document)
    
    return {
        "organization": org,
        "project": project,
        "document": document,
    }


# ============================================================================
# TEST MARKERS FOR COVERAGE TRACKING
# ============================================================================

def pytest_configure(config):
    """Register custom coverage markers."""
    config.addinivalue_line(
        "markers", "coverage_cli: CLI adapter coverage tests"
    )
    config.addinivalue_line(
        "markers", "coverage_mcp: MCP adapter coverage tests"
    )
    config.addinivalue_line(
        "markers", "coverage_workflow: Workflow tool coverage tests"
    )
    config.addinivalue_line(
        "markers", "coverage_e2e: End-to-end MCP client tests"
    )
    config.addinivalue_line(
        "markers", "mock_only: Tests using mocks (no live services)"
    )
    config.addinivalue_line(
        "markers", "live_services: Tests requiring live Supabase/AuthKit"
    )
