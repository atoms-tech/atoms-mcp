# Atoms MCP - API Reference

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Common Patterns](#common-patterns)
- [Entity Management API](#entity-management-api)
- [Search API](#search-api)
- [MCP Tools API](#mcp-tools-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [SDK Examples](#sdk-examples)

## Overview

The Atoms MCP API provides comprehensive endpoints for managing knowledge management entities including organizations, projects, documents, requirements, and tests. The API follows RESTful principles and supports both traditional HTTP requests and Model Context Protocol (MCP) tool calls.

### API Versions
- **Current Version**: v1
- **Base URL**: `https://mcp.atoms.tech/api/v1`
- **Content Type**: `application/json`

## Authentication

All API requests require authentication via JWT token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Getting an Access Token

```python
import requests

# Step 1: Get authorization URL
response = requests.get("https://mcp.atoms.tech/auth/login")
auth_url = response.json()["auth_url"]

# Step 2: User completes OAuth flow (redirect to auth_url)
# Step 3: Exchange authorization code for token
token_response = requests.post("https://mcp.atoms.tech/auth/token", {
    "code": "authorization_code_from_callback"
})
access_token = token_response.json()["access_token"]
```

## Base URL

| Environment | Base URL | Description |
|-------------|----------|-------------|
| Production | `https://mcp.atoms.tech` | Live production environment |
| Development | `https://devmcp.atoms.tech` | Development environment |
| Local | `http://localhost:8000` | Local development server |

## Common Patterns

### Request Format

All API requests use JSON format:

```http
POST /api/entities
Content-Type: application/json
Authorization: Bearer <token>

{
    "entity_type": "organization",
    "data": {
        "name": "Acme Corporation",
        "description": "Software development company"
    }
}
```

### Response Format

#### Success Response

```json
{
    "success": true,
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Acme Corporation",
        "description": "Software development company",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    "message": "Operation completed successfully",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Response

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "field": "email",
            "issue": "Invalid email format"
        }
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Paginated Response

```json
{
    "success": true,
    "data": {
        "items": [...],
        "pagination": {
            "total": 100,
            "limit": 10,
            "offset": 0,
            "has_next": true,
            "has_prev": false
        }
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## Entity Management API

### Create Entity

Creates a new entity of the specified type.

```http
POST /api/entities
```

**Request Body:**
```json
{
    "entity_type": "organization|project|document|requirement|test",
    "data": {
        // Entity-specific data
    }
}
```

**Response:**
- `201 Created` - Entity created successfully
- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions

**Example - Create Organization:**

```bash
curl -X POST https://mcp.atoms.tech/api/entities \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "entity_type": "organization",
    "data": {
      "name": "Acme Corporation",
      "description": "Software development company",
      "settings": {
        "theme": "dark",
        "timezone": "UTC"
      }
    }
  }'
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Acme Corporation",
        "description": "Software development company",
        "settings": {
            "theme": "dark",
            "timezone": "UTC"
        },
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    "message": "Organization created successfully"
}
```

**Example - Create Project:**

```bash
curl -X POST https://mcp.atoms.tech/api/entities \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "entity_type": "project",
    "data": {
      "organization_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Mobile App MVP",
      "description": "Minimum viable product for mobile application",
      "status": "active",
      "settings": {
        "requirement_format": "EARS",
        "test_framework": "pytest"
      }
    }
  }'
```

**Example - Create Requirement (EARS Format):**

```bash
curl -X POST https://mcp.atoms.tech/api/entities \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "entity_type": "requirement",
    "data": {
      "document_id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "User Authentication",
      "description": "Users must be able to authenticate to access the system",
      "format": "EARS",
      "statement": "The system SHALL allow users to authenticate using email and password",
      "rationale": "Users need secure access to the system",
      "priority": "high",
      "status": "draft",
      "verification_method": "test"
    }
  }'
```

### Get Entity

Retrieves a specific entity by ID.

```http
GET /api/entities/{entity_id}
```

**Path Parameters:**
- `entity_id` (string, required) - UUID of the entity

**Response:**
- `200 OK` - Entity retrieved successfully
- `404 Not Found` - Entity not found
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions

**Example:**

```bash
curl -X GET https://mcp.atoms.tech/api/entities/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Acme Corporation",
        "description": "Software development company",
        "settings": {
            "theme": "dark",
            "timezone": "UTC"
        },
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
}
```

### Update Entity

Updates an existing entity.

```http
PUT /api/entities/{entity_id}
```

**Path Parameters:**
- `entity_id` (string, required) - UUID of the entity

**Request Body:**
```json
{
    "data": {
        // Fields to update
    }
}
```

**Response:**
- `200 OK` - Entity updated successfully
- `400 Bad Request` - Invalid input data
- `404 Not Found` - Entity not found
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions

**Example:**

```bash
curl -X PUT https://mcp.atoms.tech/api/entities/123e4567-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "data": {
      "name": "Acme Corporation Inc.",
      "description": "Leading software development company"
    }
  }'
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Acme Corporation Inc.",
        "description": "Leading software development company",
        "settings": {
            "theme": "dark",
            "timezone": "UTC"
        },
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:35:00Z"
    },
    "message": "Entity updated successfully"
}
```

### Delete Entity

Soft deletes an entity (marks as deleted but preserves data).

```http
DELETE /api/entities/{entity_id}
```

**Path Parameters:**
- `entity_id` (string, required) - UUID of the entity

**Response:**
- `200 OK` - Entity deleted successfully
- `404 Not Found` - Entity not found
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions

**Example:**

```bash
curl -X DELETE https://mcp.atoms.tech/api/entities/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
    "success": true,
    "message": "Entity deleted successfully"
}
```

### List Entities

Lists entities with optional filtering and pagination.

```http
GET /api/entities
```

**Query Parameters:**
- `entity_type` (string, required) - Type of entity to list
- `limit` (integer, optional) - Maximum number of results (default: 100, max: 1000)
- `offset` (integer, optional) - Number of results to skip (default: 0)
- `filters` (object, optional) - Filter criteria (JSON string)
- `sort` (string, optional) - Sort field (default: created_at)
- `order` (string, optional) - Sort order: asc or desc (default: desc)

**Response:**
- `200 OK` - Entities retrieved successfully
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions

**Example - List Organizations:**

```bash
curl -X GET "https://mcp.atoms.tech/api/entities?entity_type=organization&limit=10&offset=0" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Acme Corporation",
                "description": "Software development company",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        ],
        "pagination": {
            "total": 1,
            "limit": 10,
            "offset": 0,
            "has_next": false,
            "has_prev": false
        }
    }
}
```

**Example - List Requirements with Filters:**

```bash
curl -X GET "https://mcp.atoms.tech/api/entities?entity_type=requirement&filters=%7B%22status%22%3A%22approved%22%2C%22priority%22%3A%22high%22%7D" \
  -H "Authorization: Bearer <token>"
```

**Note:** The `filters` parameter is URL-encoded JSON. The decoded value is:
```json
{
    "status": "approved",
    "priority": "high"
}
```

## Search API

### Semantic Search

Performs vector-based semantic search on entities.

```http
POST /api/search/semantic
```

**Request Body:**
```json
{
    "query": "user authentication requirements",
    "entity_types": ["requirement", "document"],
    "limit": 10,
    "threshold": 0.7,
    "filters": {
        "status": "approved"
    }
}
```

**Parameters:**
- `query` (string, required) - Search query
- `entity_types` (array, optional) - Types of entities to search
- `limit` (integer, optional) - Maximum number of results (default: 10, max: 100)
- `threshold` (float, optional) - Similarity threshold (0.0-1.0, default: 0.7)
- `filters` (object, optional) - Additional filter criteria

**Response:**
- `200 OK` - Search completed successfully
- `400 Bad Request` - Invalid search parameters
- `401 Unauthorized` - Invalid or missing token

**Example:**

```bash
curl -X POST https://mcp.atoms.tech/api/search/semantic \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "query": "user authentication requirements",
    "entity_types": ["requirement", "document"],
    "limit": 5,
    "threshold": 0.8
  }'
```

**Response:**
```json
{
    "success": true,
    "data": {
        "results": [
            {
                "id": "req-001",
                "title": "User Authentication Requirements",
                "content": "The system shall authenticate users using secure methods...",
                "score": 0.95,
                "entity_type": "requirement",
                "metadata": {
                    "priority": "high",
                    "status": "approved"
                }
            },
            {
                "id": "doc-001",
                "title": "Security Requirements Document",
                "content": "This document outlines all security requirements including user authentication...",
                "score": 0.87,
                "entity_type": "document",
                "metadata": {
                    "document_type": "requirement"
                }
            }
        ],
        "total": 2,
        "query": "user authentication requirements",
        "search_type": "semantic"
    }
}
```

### Full-Text Search

Performs traditional text-based search on entities.

```http
POST /api/search/text
```

**Request Body:**
```json
{
    "query": "login password security",
    "entity_types": ["requirement", "test"],
    "limit": 10,
    "filters": {
        "status": "active"
    }
}
```

**Parameters:**
- `query` (string, required) - Search query
- `entity_types` (array, optional) - Types of entities to search
- `limit` (integer, optional) - Maximum number of results (default: 10, max: 100)
- `filters` (object, optional) - Additional filter criteria

**Response:**
- `200 OK` - Search completed successfully
- `400 Bad Request` - Invalid search parameters
- `401 Unauthorized` - Invalid or missing token

**Example:**

```bash
curl -X POST https://mcp.atoms.tech/api/search/text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "query": "login password security",
    "entity_types": ["requirement", "test"],
    "limit": 5
  }'
```

**Response:**
```json
{
    "success": true,
    "data": {
        "results": [
            {
                "id": "req-002",
                "title": "User Login Requirements",
                "content": "Users must provide login credentials and password for authentication...",
                "score": 0.85,
                "entity_type": "requirement",
                "metadata": {
                    "priority": "high",
                    "status": "active"
                }
            }
        ],
        "total": 1,
        "query": "login password security",
        "search_type": "text"
    }
}
```

### Hybrid Search

Combines semantic and text search for comprehensive results.

```http
POST /api/search/hybrid
```

**Request Body:**
```json
{
    "query": "user authentication requirements",
    "entity_types": ["requirement", "document"],
    "limit": 10,
    "semantic_weight": 0.7,
    "text_weight": 0.3,
    "threshold": 0.6
}
```

**Parameters:**
- `query` (string, required) - Search query
- `entity_types` (array, optional) - Types of entities to search
- `limit` (integer, optional) - Maximum number of results (default: 10, max: 100)
- `semantic_weight` (float, optional) - Weight for semantic search (0.0-1.0, default: 0.7)
- `text_weight` (float, optional) - Weight for text search (0.0-1.0, default: 0.3)
- `threshold` (float, optional) - Combined similarity threshold (0.0-1.0, default: 0.6)
- `filters` (object, optional) - Additional filter criteria

## MCP Tools API

The MCP Tools API provides Model Context Protocol endpoints for AI agent interaction.

### Entity Tool

Universal tool for entity management operations.

```http
POST /api/mcp/tools/entity
```

**Request Body:**
```json
{
    "entity_type": "organization|project|document|requirement|test",
    "operation": "create|read|update|delete|list",
    "data": {
        // Entity data (for create/update operations)
    },
    "entity_id": "uuid",
    "filters": {
        // Filter criteria (for list operations)
    },
    "limit": 100,
    "offset": 0
}
```

**Example - Create Organization via MCP:**

```bash
curl -X POST https://mcp.atoms.tech/api/mcp/tools/entity \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "entity_type": "organization",
    "operation": "create",
    "data": {
      "name": "Tech Startup Inc.",
      "description": "Innovative technology startup"
    }
  }'
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Tech Startup Inc.",
        "description": "Innovative technology startup",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    "operation": "create",
    "entity_type": "organization"
}
```

### Search Tool

Tool for searching entities using various search methods.

```http
POST /api/mcp/tools/search
```

**Request Body:**
```json
{
    "query": "user authentication requirements",
    "entity_types": ["requirement", "document"],
    "search_type": "semantic|text|hybrid",
    "limit": 10,
    "threshold": 0.7,
    "filters": {
        "status": "approved"
    }
}
```

**Example:**

```bash
curl -X POST https://mcp.atoms.tech/api/mcp/tools/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "query": "user authentication requirements",
    "entity_types": ["requirement"],
    "search_type": "semantic",
    "limit": 5,
    "threshold": 0.8
  }'
```

**Response:**
```json
{
    "success": true,
    "data": {
        "results": [
            {
                "id": "req-001",
                "title": "User Authentication Requirements",
                "content": "The system shall authenticate users...",
                "score": 0.95,
                "entity_type": "requirement"
            }
        ],
        "query": "user authentication requirements",
        "search_type": "semantic",
        "total": 1
    }
}
```

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

### Error Response Format

```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error message",
        "details": {
            "field": "field_name",
            "issue": "Specific issue description"
        }
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `VALIDATION_ERROR` | Input validation failed | Check request data format |
| `AUTHENTICATION_ERROR` | Invalid or missing token | Re-authenticate |
| `AUTHORIZATION_ERROR` | Insufficient permissions | Check user permissions |
| `NOT_FOUND` | Resource not found | Verify resource ID |
| `DUPLICATE_ENTITY` | Entity already exists | Use different identifier |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry |
| `INTERNAL_ERROR` | Server error | Contact support |

### Error Handling Examples

```python
import requests

def handle_api_error(response):
    """Handle API error responses."""
    if response.status_code == 200:
        return response.json()
    
    error_data = response.json()
    error = error_data.get("error", {})
    
    if response.status_code == 400:
        print(f"Validation error: {error.get('message')}")
        if "details" in error:
            print(f"Field: {error['details'].get('field')}")
            print(f"Issue: {error['details'].get('issue')}")
    
    elif response.status_code == 401:
        print("Authentication error: Please re-authenticate")
    
    elif response.status_code == 403:
        print("Authorization error: Insufficient permissions")
    
    elif response.status_code == 404:
        print("Resource not found")
    
    elif response.status_code == 429:
        print("Rate limit exceeded: Please wait and retry")
    
    else:
        print(f"Server error: {error.get('message', 'Unknown error')}")
    
    return None

# Example usage
response = requests.post("https://mcp.atoms.tech/api/entities", 
                        json=data, headers=headers)
result = handle_api_error(response)
```

## Rate Limiting

### Rate Limits

| Tier | Requests per Minute | Burst Limit |
|------|-------------------|-------------|
| Free | 100 | 200 |
| Pro | 1,000 | 2,000 |
| Enterprise | Custom | Custom |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1642248000
X-RateLimit-Retry-After: 60
```

### Handling Rate Limits

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retry():
    """Create requests session with retry strategy."""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def make_request_with_rate_limit_handling(url, data, headers):
    """Make request with rate limit handling."""
    session = create_session_with_retry()
    
    response = session.post(url, json=data, headers=headers)
    
    if response.status_code == 429:
        retry_after = int(response.headers.get('X-RateLimit-Retry-After', 60))
        print(f"Rate limited. Retrying after {retry_after} seconds...")
        time.sleep(retry_after)
        return make_request_with_rate_limit_handling(url, data, headers)
    
    return response
```

## SDK Examples

### Python SDK

```python
from atoms_mcp import AtomsClient

# Initialize client
client = AtomsClient(
    base_url="https://mcp.atoms.tech",
    api_key="your-api-key"
)

# Create organization
org = client.organizations.create({
    "name": "Acme Corporation",
    "description": "Software development company"
})

# Create project
project = client.projects.create({
    "organization_id": org["id"],
    "name": "Mobile App MVP",
    "description": "Minimum viable product"
})

# Create requirement
requirement = client.requirements.create({
    "document_id": document["id"],
    "title": "User Authentication",
    "description": "Users must be able to authenticate",
    "format": "EARS",
    "statement": "The system SHALL allow users to authenticate",
    "rationale": "Users need secure access",
    "priority": "high"
})

# Search requirements
results = client.search.semantic(
    query="user authentication requirements",
    entity_types=["requirement"],
    limit=10
)
```

### JavaScript SDK

```javascript
import { AtomsClient } from '@atoms/mcp-client';

// Initialize client
const client = new AtomsClient({
    baseUrl: 'https://mcp.atoms.tech',
    apiKey: 'your-api-key'
});

// Create organization
const org = await client.organizations.create({
    name: 'Acme Corporation',
    description: 'Software development company'
});

// Create project
const project = await client.projects.create({
    organizationId: org.id,
    name: 'Mobile App MVP',
    description: 'Minimum viable product'
});

// Search requirements
const results = await client.search.semantic({
    query: 'user authentication requirements',
    entityTypes: ['requirement'],
    limit: 10
});
```

### cURL Examples

```bash
# Set up variables
BASE_URL="https://mcp.atoms.tech"
TOKEN="your-jwt-token"

# Create organization
curl -X POST "$BASE_URL/api/entities" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "entity_type": "organization",
    "data": {
      "name": "Acme Corporation",
      "description": "Software development company"
    }
  }'

# List projects
curl -X GET "$BASE_URL/api/entities?entity_type=project&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Search requirements
curl -X POST "$BASE_URL/api/search/semantic" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "user authentication requirements",
    "entity_types": ["requirement"],
    "limit": 5
  }'
```

This API reference provides comprehensive documentation for all Atoms MCP API endpoints. For additional help, contact support@atoms.tech or check the project's GitHub repository.