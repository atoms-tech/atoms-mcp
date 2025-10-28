"""Comprehensive mock framework for external dependencies."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest


# Database and external service mocks
class MockSupabaseClient:
    """Mock Supabase client for testing."""

    def __init__(self):
        self.tables = {}
        self.auth = Mock()
        self.auth.admin = Mock()

    def table(self, table_name):
        return MockTable(table_name, self)

    def rpc(self, func_name):
        return MockRPC(func_name, self)

    def from_(self, table_name):
        return self.table(table_name)

    def auth_user(self):
        return {"id": "test-user", "email": "test@example.com"}


class MockTable:
    """Mock database table."""

    def __init__(self, name, client):
        self.name = name
        self.client = client
        self.data = client.tables.get(name, [])

    def select(self, columns="*"):
        mock = Mock()
        mock.eq = self._eq
        mock.or_ = self._or_
        mock.and_ = self._and_
        mock.in_ = self._in_
        mock.execute = self._execute_select
        return mock

    def insert(self, data):
        mock = Mock()
        mock.execute = self._execute_insert(data)
        return mock

    def update(self, data):
        mock = Mock()
        mock.execute = self._execute_update(data)
        return mock

    def delete(self):
        mock = Mock()
        mock.execute = self._execute_delete
        return mock

    def _eq(self, field, value):
        self._eq_field = field
        self._eq_value = value
        return self

    def _or_(self, condition):
        self._or_condition = condition
        return self

    def _and_(self, condition):
        self._and_condition = condition
        return self

    def _in_(self, field, values):
        self._in_field = field
        self._in_values = values
        return self

    def _execute_select(self):
        # Filter data based on conditions
        filtered_data = self.data.copy()

        if hasattr(self, "_eq_field"):
            filtered_data = [item for item in filtered_data
                           if item.get(self._eq_field) == self._eq_value]

        response = Mock()
        response.data = filtered_data
        return response

    def _execute_insert(self, data):
        # Add new record
        if isinstance(data, list):
            self.data.extend(data)
        else:
            self.data.append(data)

        response = Mock()
        response.data = data if isinstance(data, list) else [data]
        return response

    def _execute_update(self, data):
        # Update records
        if hasattr(self, "_eq_field"):
            for item in self.data:
                if item.get(self._eq_field) == self._eq_value:
                    item.update(data)

        filtered_data = [item for item in self.data
                        if item.get(self._eq_field) == self._eq_value] if hasattr(self, "_eq_field") else self.data

        response = Mock()
        response.data = filtered_data
        return response

    def _execute_delete(self):
        # Delete records
        if hasattr(self, "_eq_field"):
            self.data = [item for item in self.data
                        if item.get(self._eq_field) != self._eq_value]

        response = Mock()
        response.data = []
        return response


class MockRPC:
    """Mock RPC function."""

    def __init__(self, name, client):
        self.name = name
        self.client = client

    def execute(self):
        response = Mock()

        # Return appropriate mock data based on RPC name
        if self.name.startswith("aggregate_"):
            response.data = [
                {"entity_type": "project", "count": 10},
                {"entity_type": "document", "count": 25}
            ]
        elif self.name.startswith("analyze_"):
            response.data = {
                "total_entities": 100,
                "active_projects": 15,
                "recent_documents": 30
            }
        else:
            response.data = []

        return response


# Mock configuration
class MockConfig:
    """Mock configuration manager."""

    def __init__(self):
        self.config = {
            "database_url": "postgresql://localhost:5432/test",
            "redis_url": "redis://localhost:6379",
            "jwt_secret": "test-secret-key",
            "debug": True,
            "environment": "test",
            "port": 8000,
            "host": "localhost"
        }

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value


# Mock external services
class MockVercelClient:
    """Mock Vercel client for deployment."""

    def __init__(self):
        self.deployments = []
        self.projects = []

    def create_deployment(self, project_id, data):
        deployment = {
            "id": f"deploy-{len(self.deployments)+1}",
            "project_id": project_id,
            "status": "ready",
            "url": f"https://test-{len(self.deployments)+1}.vercel.app",
            "created_at": datetime.now(UTC).isoformat(),
            **data
        }
        self.deployments.append(deployment)
        return deployment

    def get_deployment(self, deployment_id):
        for deployment in self.deployments:
            if deployment["id"] == deployment_id:
                return deployment
        return None

    def list_deployments(self, project_id):
        return [d for d in self.deployments if d["project_id"] == project_id]


class MockRedisClient:
    """Mock Redis client."""

    def __init__(self):
        self.data = {}
        self.expires = {}

    def set(self, key, value, ex=None):
        self.data[key] = value
        if ex:
            self.expires[key] = datetime.now(UTC) + timedelta(seconds=ex)

    def get(self, key):
        # Check expiration
        if key in self.expires and datetime.now(UTC) > self.expires[key]:
            del self.data[key]
            del self.expires[key]
            return None
        return self.data.get(key)

    def delete(self, key):
        self.data.pop(key, None)
        self.expires.pop(key, None)

    def exists(self, key):
        return self.get(key) is not None


# Mock authentication
class MockAuthSystem:
    """Mock authentication system."""

    def __init__(self):
        self.users = {
            "test-user": {
                "id": "test-user",
                "email": "test@example.com",
                "password_hash": "hashed_password",
                "role": "admin",
                "created_at": datetime.now(UTC).isoformat()
            }
        }
        self.tokens = {}
        self.refresh_tokens = {}

    def authenticate(self, email, password):
        """Authenticate user and return tokens."""
        for user_id, user_data in self.users.items():
            if user_data["email"] == email:
                # In mock, accept any password for test user
                access_token = f"access-{user_id}"
                refresh_token = f"refresh-{user_id}"
                expires_at = datetime.now(UTC) + timedelta(hours=1)

                self.tokens[access_token] = {
                    "user_id": user_id,
                    "expires_at": expires_at
                }
                self.refresh_tokens[refresh_token] = user_id

                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at,
                    "user": user_data
                }
        return None

    def validate_token(self, access_token):
        """Validate access token."""
        token_data = self.tokens.get(access_token)
        if token_data and datetime.now(UTC) < token_data["expires_at"]:
            return {
                "user_id": token_data["user_id"],
                "valid": True
            }
        return {"valid": False}

    def refresh_token(self, refresh_token):
        """Refresh access token."""
        user_id = self.refresh_tokens.get(refresh_token)
        if user_id and user_id in self.users:
            new_access_token = f"new-access-{user_id}"
            expires_at = datetime.now(UTC) + timedelta(hours=1)

            self.tokens[new_access_token] = {
                "user_id": user_id,
                "expires_at": expires_at
            }

            return {
                "access_token": new_access_token,
                "expires_at": expires_at
            }
        return None


# Mock file system and storage
class MockFileSystem:
    """Mock file system for testing."""

    def __init__(self):
        self.files = {}
        self.directories = set()

    def write_file(self, path, content):
        """Write file content."""
        self.files[path] = content

        # Ensure parent directory exists
        dir_path = "/".join(path.split("/")[:-1])
        if dir_path:
            self.directories.add(dir_path)

    def read_file(self, path):
        """Read file content."""
        return self.files.get(path)

    def file_exists(self, path):
        """Check if file exists."""
        return path in self.files

    def create_directory(self, path):
        """Create directory."""
        self.directories.add(path)

    def directory_exists(self, path):
        """Check if directory exists."""
        return path in self.directories

    def list_directory(self, path):
        """List directory contents."""
        files = []
        for file_path in self.files:
            if file_path.startswith(path + "/"):
                files.append(file_path[len(path)+1:])
        return files


# Mock HTTP client
class MockHttpClient:
    """Mock HTTP client for external API calls."""

    def __init__(self):
        self.responses = {}
        self.requests = []

    def add_response(self, method, url, response_data, status_code=200):
        """Add a canned response."""
        key = f"{method.upper()}:{url}"
        self.responses[key] = {
            "data": response_data,
            "status": status_code
        }

    def get(self, url, headers=None):
        """Mock GET request."""
        return self._make_request("GET", url, None, headers)

    def post(self, url, data=None, json=None, headers=None):
        """Mock POST request."""
        return self._make_request("POST", url, json or data, headers)

    def put(self, url, data=None, json=None, headers=None):
        """Mock PUT request."""
        return self._make_request("PUT", url, json or data, headers)

    def delete(self, url, headers=None):
        """Mock DELETE request."""
        return self._make_request("DELETE", url, None, headers)

    def _make_request(self, method, url, data, headers):
        """Make mock HTTP request."""
        self.requests.append({
            "method": method,
            "url": url,
            "data": data,
            "headers": headers or {}
        })

        key = f"{method.upper()}:{url}"
        response = self.responses.get(key)

        if response:
            return MockHttpResponse(
                data=response["data"],
                status=response["status"]
            )

        # Default 404 response
        return MockHttpResponse(status=404, data={"error": "Not found"})


class MockHttpResponse:
    """Mock HTTP response."""

    def __init__(self, data=None, status=200, headers=None):
        self.data = data or {}
        self.status_code = status
        self.headers = headers or {}
        self.text = json.dumps(data) if isinstance(data, (dict, list)) else str(data)

    def json(self):
        """Return JSON data."""
        return self.data

    def raise_for_status(self):
        """Raise error for bad status codes."""
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}: {self.data}")


# Test fixtures and utilities
@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client fixture."""
    return MockSupabaseClient()


@pytest.fixture
def mock_config():
    """Mock configuration fixture."""
    return MockConfig()


@pytest.fixture
def mock_vercel_client():
    """Mock Vercel client fixture."""
    return MockVercelClient()


@pytest.fixture
def mock_redis_client():
    """Mock Redis client fixture."""
    return MockRedisClient()


@pytest.fixture
def mock_auth_system():
    """Mock auth system fixture."""
    return MockAuthSystem()


@pytest.fixture
def mock_file_system():
    """Mock file system fixture."""
    return MockFileSystem()


@pytest.fixture
def mock_http_client():
    """Mock HTTP client fixture."""
    return MockHttpClient()


# Mock decorators and context managers
class mock_supabase_client:
    """Mock Supabase client context manager."""

    def __init__(self, client=None):
        self.client = client or MockSupabaseClient()
        self.patcher = None

    def __enter__(self):
        self.patcher = patch("server.core.get_supabase_client")
        self.patcher.return_value = self.client
        self.patcher.start()
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.patcher:
            self.patcher.stop()


class mock_external_services:
    """Mock multiple external services context manager."""

    def __init__(self, supabase=None, redis=None, vercel=None):
        self.supabase = supabase or MockSupabaseClient()
        self.redis = redis or MockRedisClient()
        self.vercel = vercel or MockVercelClient()
        self.patchers = []

    def __enter__(self):
        # Patch all external services
        self.patchers.append(patch("server.core.get_supabase_client", return_value=self.supabase))
        self.patchers.append(patch("server.core.get_redis_client", return_value=self.redis))
        self.patchers.append(patch("lib.deployment_checker.get_vercel_client", return_value=self.vercel))

        for patcher in self.patchers:
            patcher.start()

        return {
            "supabase": self.supabase,
            "redis": self.redis,
            "vercel": self.vercel
        }

    def __exit__(self, exc_type, exc_val, exc_tb):
        for patcher in self.patchers:
            patcher.stop()


# Utility functions for test data creation
def create_test_user(user_id="test-user", email="test@example.com"):
    """Create test user data."""
    return {
        "id": user_id,
        "email": email,
        "role": "user",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat()
    }


def create_test_project(project_id="proj-1", name="Test Project", owner_id="test-user"):
    """Create test project data."""
    return {
        "id": project_id,
        "name": name,
        "slug": name.lower().replace(" ", "-"),
        "description": "A test project",
        "owner_id": owner_id,
        "status": "active",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat()
    }


def create_test_document(doc_id="doc-1", title="Test Document", project_id="proj-1"):
    """Create test document data."""
    return {
        "id": doc_id,
        "title": title,
        "content": "This is a test document content.",
        "project_id": project_id,
        "status": "active",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat()
    }


def create_test_requirement(req_id="req-1", title="Test Requirement", doc_id="doc-1"):
    """Create test requirement data."""
    return {
        "id": req_id,
        "title": title,
        "description": "This is a test requirement description.",
        "document_id": doc_id,
        "priority": "high",
        "status": "active",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat()
    }


def create_test_organization(org_id="org-1", name="Test Organization", owner_id="test-user"):
    """Create test organization data."""
    return {
        "id": org_id,
        "name": name,
        "slug": name.lower().replace(" ", "-"),
        "description": "A test organization",
        "owner_id": owner_id,
        "type": "team",
        "status": "active",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat()
    }


# Mock environment variables
def mock_env_vars(env_dict):
    """Mock environment variables."""
    return patch.dict("os.environ", env_dict)


# Async test utilities
class AsyncTestUtils:
    """Utilities for async testing."""

    @staticmethod
    def create_async_mock(return_value=None, side_effect=None):
        """Create async mock with proper signature."""
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock

    @staticmethod
    async def run_parallel(*coroutines):
        """Run coroutines in parallel."""
        import asyncio
        return await asyncio.gather(*coroutines)

    @staticmethod
    def assert_awaited(mock):
        """Assert async mock was awaited."""
        mock.assert_awaited()
        if hasattr(mock, "assert_awaited_once"):
            mock.assert_awaited_once()


# Performance testing utilities
class PerformanceTestUtils:
    """Utilities for performance testing."""

    @staticmethod
    def time_function(func, *args, **kwargs):
        """Time function execution."""
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time

    @staticmethod
    def time_async_function(coro):
        """Time async coroutine execution."""
        import asyncio
        import time
        start_time = time.time()
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(coro)
        end_time = time.time()
        return result, end_time - start_time

    @staticmethod
    def assert_execution_time(max_seconds):
        """Decorator to assert execution time."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                result, execution_time = PerformanceTestUtils.time_function(func, *args, **kwargs)
                assert execution_time < max_seconds, f"Function took {execution_time}s, expected < {max_seconds}s"
                return result
            return wrapper
        return decorator


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""

    def __init__(self, mock_client=None):
        self.client = mock_client or MockSupabaseClient()
        self.user_counter = 1
        self.project_counter = 1
        self.document_counter = 1
        self.requirement_counter = 1
        self.organization_counter = 1

    def create_user(self, **overrides):
        """Create a test user."""
        user_id = f"user-{self.user_counter}"
        self.user_counter += 1

        return create_test_user(user_id=user_id, **overrides)

    def create_project(self, **overrides):
        """Create a test project."""
        project_id = f"proj-{self.project_counter}"
        self.project_counter += 1

        project = create_test_project(project_id=project_id, **overrides)
        self.client.tables.get("projects", []).append(project)
        return project

    def create_document(self, **overrides):
        """Create a test document."""
        doc_id = f"doc-{self.document_counter}"
        self.document_counter += 1

        document = create_test_document(doc_id=doc_id, **overrides)
        self.client.tables.get("documents", []).append(document)
        return document

    def create_requirement(self, **overrides):
        """Create a test requirement."""
        req_id = f"req-{self.requirement_counter}"
        self.requirement_counter += 1

        requirement = create_test_requirement(req_id=req_id, **overrides)
        self.client.tables.get("requirements", []).append(requirement)
        return requirement

    def create_organization(self, **overrides):
        """Create a test organization."""
        org_id = f"org-{self.organization_counter}"
        self.organization_counter += 1

        organization = create_test_organization(org_id=org_id, **overrides)
        self.client.tables.get("organizations", []).append(organization)
        return organization

    def create_project_with_docs_and_requirements(self, **overrides):
        """Create a complete project with documents and requirements."""
        project = self.create_project(**overrides)

        # Create documents
        doc1 = self.create_document(
            title="Requirements Document",
            project_id=project["id"]
        )
        doc2 = self.create_document(
            title="Design Document",
            project_id=project["id"]
        )

        # Create requirements
        req1 = self.create_requirement(
            title="Login Functionality",
            document_id=doc1["id"]
        )
        req2 = self.create_requirement(
            title="User Registration",
            document_id=doc1["id"]
        )

        return {
            "project": project,
            "documents": [doc1, doc2],
            "requirements": [req1, req2]
        }


# Integration test utilities
class IntegrationTestUtils:
    """Utilities for integration testing."""

    @staticmethod
    def setup_complete_environment():
        """Setup complete test environment with all services."""
        return mock_external_services()

    @staticmethod
    def create_test_scenario(scenario_type="basic"):
        """Create different test scenarios."""
        factory = TestDataFactory()

        if scenario_type == "basic":
            return factory.create_project_with_docs_and_requirements()

        if scenario_type == "multi_project":
            org = factory.create_organization(name="Test Org")
            proj1 = factory.create_project(name="Project 1")
            proj2 = factory.create_project(name="Project 2")
            return {"organization": org, "projects": [proj1, proj2]}

        if scenario_type == "complex":
            # Create complex scenario with multiple entities
            org = factory.create_organization()
            proj1 = factory.create_project()
            proj2 = factory.create_project()
            doc1 = factory.create_document(project_id=proj1["id"])
            doc2 = factory.create_document(project_id=proj2["id"])
            req1 = factory.create_requirement(document_id=doc1["id"])
            req2 = factory.create_requirement(document_id=doc2["id"])

            return {
                "organization": org,
                "projects": [proj1, proj2],
                "documents": [doc1, doc2],
                "requirements": [req1, req2]
            }

        return None
