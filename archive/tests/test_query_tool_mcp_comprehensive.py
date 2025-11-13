"""
Comprehensive MCP test suite for mcp__Atoms__query_tool

Tests all query types through the actual MCP interface:
1. SEARCH - Cross-entity text search
2. AGGREGATE - Summary statistics and counts
3. ANALYZE - Deep analysis with relationships
4. RELATIONSHIPS - Relationship analysis
5. RAG_SEARCH - AI-powered semantic search (all modes: auto, semantic, keyword, hybrid)
6. SIMILARITY - Find similar content

This script creates test data, runs all query operations through MCP, documents results, and cleans up.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supabase import create_client, Client  # noqa: E402


class MCPQueryToolTester:
    """Comprehensive tester for query tool operations through MCP."""

    def __init__(self):
        # Initialize Supabase client
        # Try both environment variable names
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL) and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Initialize MCP tool
        self.auth_token = None
        self.test_results = {
            "test_run_id": datetime.utcnow().isoformat(),
            "environment": "test",
            "query_types_tested": [],
            "test_data_created": {},
            "test_results": {},
            "errors": [],
            "summary": {}
        }
        self.test_data_ids = {
            "organizations": [],
            "projects": [],
            "documents": [],
            "requirements": [],
            "tests": [],
            "users": []
        }

    async def initialize_auth(self):
        """Initialize authentication."""
        print("\n🔑 Initializing authentication...")

        try:
            # Use admin credentials or service role
            # For testing, we'll use the service role key directly
            self.auth_token = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            print("  ✅ Authentication initialized")

        except Exception as e:
            error_msg = f"Failed to initialize authentication: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.test_results["errors"].append({
                "phase": "auth_init",
                "error": error_msg
            })
            raise

    async def cleanup_existing_test_data(self):
        """Clean up any existing test data from previous runs."""
        print("\n🧹 Cleaning up any existing test data...")

        try:
            # Delete test organizations by name pattern
            orgs = self.supabase.table("organizations").select("id").or_(
                "name.like.*MCP Query Test*,name.like.*AI Research Labs MCP*,name.like.*Vector Search Inc*"
            ).execute()

            for org in orgs.data:
                # Delete organization members first
                self.supabase.table("organization_members").delete().eq("organization_id", org["id"]).execute()
                # Delete projects and related data
                projects = self.supabase.table("projects").select("id").eq("organization_id", org["id"]).execute()
                for proj in projects.data:
                    # Delete project members
                    self.supabase.table("project_members").delete().eq("project_id", proj["id"]).execute()
                    # Delete documents and related
                    docs = self.supabase.table("documents").select("id").eq("project_id", proj["id"]).execute()
                    for doc in docs.data:
                        # Delete requirements
                        reqs = self.supabase.table("requirements").select("id").eq("document_id", doc["id"]).execute()
                        for req in reqs.data:
                            # Delete requirement_tests
                            self.supabase.table("requirement_tests").delete().eq("requirement_id", req["id"]).execute()
                            # Delete requirement
                            self.supabase.table("requirements").delete().eq("id", req["id"]).execute()
                        # Delete document
                        self.supabase.table("documents").delete().eq("id", doc["id"]).execute()
                    # Delete tests
                    self.supabase.table("tests").delete().eq("project_id", proj["id"]).execute()
                    # Delete project
                    self.supabase.table("projects").delete().eq("id", proj["id"]).execute()
                # Delete organization
                self.supabase.table("organizations").delete().eq("id", org["id"]).execute()

            print("  ✅ Cleaned up existing test data")
        except Exception as e:
            print(f"  ⚠️  Warning during cleanup: {str(e)}")

    async def setup_test_data(self):
        """Create diverse test data for comprehensive testing."""
        print("\n🔧 Setting up test data...")

        try:
            # Get an existing user ID from the database
            # Try to get from existing organizations first
            try:
                orgs = self.supabase.table("organizations").select("created_by").limit(1).execute()
                if orgs.data and len(orgs.data) > 0:
                    user_id = orgs.data[0]["created_by"]
                else:
                    # Try from projects
                    projects = self.supabase.table("projects").select("created_by").limit(1).execute()
                    if projects.data and len(projects.data) > 0:
                        user_id = projects.data[0]["created_by"]
                    else:
                        raise ValueError("No existing user IDs found in database")

            except Exception as e:
                raise ValueError(f"Could not find existing user ID: {str(e)}")

            self.test_data_ids["users"].append(user_id)
            print(f"  ✅ Using existing user ID: {user_id[:8]}...")

            # 1. Create test organizations
            orgs_data = [
                {
                    "name": "MCP Query Test Corp",
                    "slug": "mcp-query-test-corp",
                    "type": "team",
                    "description": "Primary organization for query testing with authentication flows and MCP integration",
                    "created_by": user_id,
                    "updated_by": user_id
                },
                {
                    "name": "AI Research Labs MCP",
                    "slug": "ai-research-labs-mcp",
                    "type": "enterprise",
                    "description": "Organization focused on machine learning, AI development, and semantic search capabilities",
                    "created_by": user_id,
                    "updated_by": user_id
                },
                {
                    "name": "Vector Search Inc",
                    "slug": "vector-search-inc",
                    "type": "team",
                    "description": "Specialized in embedding-based retrieval and hybrid search algorithms",
                    "created_by": user_id,
                    "updated_by": user_id
                }
            ]

            for org_data in orgs_data:
                result = self.supabase.table("organizations").insert(org_data).execute()
                if result.data:
                    org_id = result.data[0]["id"]
                    self.test_data_ids["organizations"].append(org_id)

                    # Add user as admin (skip if already exists due to trigger)
                    try:
                        self.supabase.table("organization_members").insert({
                            "organization_id": org_id,
                            "user_id": user_id,
                            "role": "admin",
                            "status": "active"
                        }).execute()
                    except Exception as e:
                        if "duplicate key" not in str(e):
                            raise

                    print(f"  ✅ Created organization: {org_data['name']}")

            # 2. Create test projects with varied content
            projects_data = [
                {
                    "name": "OAuth2 Authentication System",
                    "slug": "oauth2-auth-system",
                    "description": "Comprehensive OAuth2 and JWT-based authentication microservice with session management, token refresh, and PKCE support",
                    "organization_id": self.test_data_ids["organizations"][0],
                    "status": "active",
                    "created_by": user_id,
                    "updated_by": user_id,
                    "owned_by": user_id
                },
                {
                    "name": "Hybrid Vector Search Engine",
                    "slug": "hybrid-vector-search",
                    "description": "High-performance semantic search engine using embeddings and hybrid retrieval combining keyword and vector similarity",
                    "organization_id": self.test_data_ids["organizations"][1],
                    "status": "active",
                    "created_by": user_id,
                    "updated_by": user_id,
                    "owned_by": user_id
                },
                {
                    "name": "ML Model Training Pipeline",
                    "slug": "ml-training-pipeline",
                    "description": "End-to-end distributed machine learning training infrastructure with GPU acceleration and model versioning",
                    "organization_id": self.test_data_ids["organizations"][1],
                    "status": "planning",
                    "created_by": user_id,
                    "updated_by": user_id,
                    "owned_by": user_id
                },
                {
                    "name": "Real-time Analytics Dashboard",
                    "slug": "analytics-dashboard",
                    "description": "Interactive dashboard with real-time data visualization and analytics processing",
                    "organization_id": self.test_data_ids["organizations"][2],
                    "status": "active",
                    "created_by": user_id,
                    "updated_by": user_id,
                    "owned_by": user_id
                }
            ]

            for proj_data in projects_data:
                result = self.supabase.table("projects").insert(proj_data).execute()
                if result.data:
                    proj_id = result.data[0]["id"]
                    self.test_data_ids["projects"].append(proj_id)

                    # Add user as project member (skip if already exists due to trigger)
                    try:
                        self.supabase.table("project_members").insert({
                            "project_id": proj_id,
                            "user_id": user_id,
                            "role": "admin",
                            "status": "active"
                        }).execute()
                    except Exception as e:
                        if "duplicate key" not in str(e):
                            raise

                    print(f"  ✅ Created project: {proj_data['name']}")

            # 3. Create documents with diverse content
            documents_data = [
                {
                    "name": "Authentication Security Requirements",
                    "description": "Detailed security requirements for OAuth2 implementation, token management, and user session handling",
                    "project_id": self.test_data_ids["projects"][0],
                    "doc_type": "requirements",
                    "created_by": user_id
                },
                {
                    "name": "Vector Search Algorithm Design",
                    "description": "Technical design for hybrid semantic and keyword search algorithms using embeddings and traditional indexing",
                    "project_id": self.test_data_ids["projects"][1],
                    "doc_type": "design",
                    "created_by": user_id
                },
                {
                    "name": "ML Training Pipeline Specifications",
                    "description": "Comprehensive specifications for distributed training with GPU acceleration and data pipeline optimization",
                    "project_id": self.test_data_ids["projects"][2],
                    "doc_type": "technical_spec",
                    "created_by": user_id
                },
                {
                    "name": "Analytics Dashboard Requirements",
                    "description": "User interface and functionality requirements for real-time analytics visualization",
                    "project_id": self.test_data_ids["projects"][3],
                    "doc_type": "requirements",
                    "created_by": user_id
                }
            ]

            for doc_data in documents_data:
                result = self.supabase.table("documents").insert(doc_data).execute()
                if result.data:
                    self.test_data_ids["documents"].append(result.data[0]["id"])
                    print(f"  ✅ Created document: {doc_data['name']}")

            # 4. Create requirements with semantic variety for RAG testing
            requirements_data = [
                # Auth system requirements
                {
                    "name": "REQ-AUTH-001",
                    "description": "System shall support OAuth2 authorization code flow with PKCE extension for secure authentication and protection against authorization code interception attacks",
                    "document_id": self.test_data_ids["documents"][0],
                    "status": "approved",
                    "priority": "high",
                    "requirement_type": "functional",
                    "created_by": user_id
                },
                {
                    "name": "REQ-AUTH-002",
                    "description": "JWT access tokens must expire after 24 hours and support automatic refresh token rotation with secure storage mechanisms",
                    "document_id": self.test_data_ids["documents"][0],
                    "status": "approved",
                    "priority": "high",
                    "requirement_type": "functional",
                    "created_by": user_id
                },
                {
                    "name": "REQ-AUTH-003",
                    "description": "User authentication must support multi-factor authentication via TOTP with backup recovery codes for account security",
                    "document_id": self.test_data_ids["documents"][0],
                    "status": "draft",
                    "priority": "medium",
                    "requirement_type": "functional",
                    "created_by": user_id
                },
                {
                    "name": "REQ-AUTH-004",
                    "description": "Session management shall implement secure cookie handling with HTTPOnly, Secure, and SameSite flags to prevent CSRF and XSS attacks",
                    "document_id": self.test_data_ids["documents"][0],
                    "status": "approved",
                    "priority": "high",
                    "requirement_type": "security",
                    "created_by": user_id
                },
                # Search requirements
                {
                    "name": "REQ-SEARCH-001",
                    "description": "Search engine shall provide semantic similarity matching using vector embeddings generated from transformer-based language models",
                    "document_id": self.test_data_ids["documents"][1],
                    "status": "approved",
                    "priority": "high",
                    "requirement_type": "functional",
                    "created_by": user_id
                },
                {
                    "name": "REQ-SEARCH-002",
                    "description": "Hybrid search must combine keyword-based BM25 scoring and semantic vector similarity with configurable weight parameters for optimal retrieval",
                    "document_id": self.test_data_ids["documents"][1],
                    "status": "approved",
                    "priority": "high",
                    "requirement_type": "functional",
                    "created_by": user_id
                },
                {
                    "name": "REQ-SEARCH-003",
                    "description": "Search response time shall not exceed 200ms for 95th percentile queries with automatic caching and index optimization",
                    "document_id": self.test_data_ids["documents"][1],
                    "status": "approved",
                    "priority": "medium",
                    "requirement_type": "performance",
                    "created_by": user_id
                },
                {
                    "name": "REQ-SEARCH-004",
                    "description": "Vector embeddings shall use dimensionality reduction techniques to optimize storage while maintaining search accuracy above 90%",
                    "document_id": self.test_data_ids["documents"][1],
                    "status": "draft",
                    "priority": "low",
                    "requirement_type": "functional",
                    "created_by": user_id
                },
                # ML requirements
                {
                    "name": "REQ-ML-001",
                    "description": "Training pipeline must support distributed training across multiple GPUs with automatic gradient synchronization and load balancing",
                    "document_id": self.test_data_ids["documents"][2],
                    "status": "draft",
                    "priority": "high",
                    "requirement_type": "functional",
                    "created_by": user_id
                },
                {
                    "name": "REQ-ML-002",
                    "description": "Model versioning system shall track hyperparameters, training datasets, validation metrics, and model artifacts with full reproducibility",
                    "document_id": self.test_data_ids["documents"][2],
                    "status": "draft",
                    "priority": "medium",
                    "requirement_type": "functional",
                    "created_by": user_id
                },
                {
                    "name": "REQ-ML-003",
                    "description": "Data preprocessing pipeline must handle streaming data with incremental learning capabilities and online model updates",
                    "document_id": self.test_data_ids["documents"][2],
                    "status": "approved",
                    "priority": "medium",
                    "requirement_type": "functional",
                    "created_by": user_id
                },
                # Analytics requirements
                {
                    "name": "REQ-ANALYTICS-001",
                    "description": "Dashboard shall render interactive visualizations with real-time data updates using WebSocket connections and efficient rendering",
                    "document_id": self.test_data_ids["documents"][3],
                    "status": "approved",
                    "priority": "high",
                    "requirement_type": "functional",
                    "created_by": user_id
                },
                {
                    "name": "REQ-ANALYTICS-002",
                    "description": "Analytics engine must support complex aggregation queries with sub-second response times for datasets up to 1 billion records",
                    "document_id": self.test_data_ids["documents"][3],
                    "status": "approved",
                    "priority": "medium",
                    "requirement_type": "performance",
                    "created_by": user_id
                }
            ]

            for req_data in requirements_data:
                result = self.supabase.table("requirements").insert(req_data).execute()
                if result.data:
                    self.test_data_ids["requirements"].append(result.data[0]["id"])

            print(f"  ✅ Created {len(requirements_data)} requirements")

            # 5. Create tests
            tests_data = [
                {
                    "title": "OAuth2 Authorization Flow Integration Test",
                    "description": "Verify complete OAuth2 authorization code flow with PKCE, token exchange, and refresh token rotation",
                    "project_id": self.test_data_ids["projects"][0],
                    "test_type": "integration",
                    "priority": "high",
                    "status": "passed",
                    "created_by": user_id
                },
                {
                    "title": "Semantic Search Relevance Test",
                    "description": "Validate search relevance using embeddings with similarity threshold tuning and precision/recall metrics",
                    "project_id": self.test_data_ids["projects"][1],
                    "test_type": "functional",
                    "priority": "high",
                    "status": "passed",
                    "created_by": user_id
                },
                {
                    "title": "Hybrid Search Performance Benchmark",
                    "description": "Measure hybrid search performance under load with varying weight configurations for optimal results",
                    "project_id": self.test_data_ids["projects"][1],
                    "test_type": "performance",
                    "priority": "medium",
                    "status": "passed",
                    "created_by": user_id
                },
                {
                    "title": "Multi-factor Authentication Test",
                    "description": "Test TOTP-based MFA with time synchronization and backup code recovery scenarios",
                    "project_id": self.test_data_ids["projects"][0],
                    "test_type": "functional",
                    "priority": "high",
                    "status": "failed",
                    "created_by": user_id
                },
                {
                    "title": "Distributed Training Scalability Test",
                    "description": "Verify distributed training scales linearly with GPU count and maintains model convergence",
                    "project_id": self.test_data_ids["projects"][2],
                    "test_type": "integration",
                    "priority": "high",
                    "status": "pending",
                    "created_by": user_id
                }
            ]

            for test_data in tests_data:
                result = self.supabase.table("tests").insert(test_data).execute()
                if result.data:
                    self.test_data_ids["tests"].append(result.data[0]["id"])

            print(f"  ✅ Created {len(tests_data)} tests")

            # 6. Create test relationships
            if len(self.test_data_ids["requirements"]) > 0 and len(self.test_data_ids["tests"]) > 0:
                relationships = [
                    (0, 0, "full"),   # First test -> First requirement
                    (1, 4, "full"),   # Second test -> Fifth requirement (REQ-SEARCH-001)
                    (2, 5, "full"),   # Third test -> Sixth requirement (REQ-SEARCH-002)
                    (3, 2, "partial"), # Fourth test -> Third requirement (REQ-AUTH-003)
                ]

                for test_idx, req_idx, coverage in relationships:
                    if test_idx < len(self.test_data_ids["tests"]) and req_idx < len(self.test_data_ids["requirements"]):
                        self.supabase.table("requirement_tests").insert({
                            "requirement_id": self.test_data_ids["requirements"][req_idx],
                            "test_id": self.test_data_ids["tests"][test_idx],
                            "relationship_type": "tests",
                            "coverage_level": coverage
                        }).execute()

                print(f"  ✅ Created {len(relationships)} test-requirement relationships")

            self.test_results["test_data_created"] = {
                "organizations": len(self.test_data_ids["organizations"]),
                "projects": len(self.test_data_ids["projects"]),
                "documents": len(self.test_data_ids["documents"]),
                "requirements": len(self.test_data_ids["requirements"]),
                "tests": len(self.test_data_ids["tests"])
            }

            print("\n✅ Test data setup complete!")
            print(f"   Organizations: {len(self.test_data_ids['organizations'])}")
            print(f"   Projects: {len(self.test_data_ids['projects'])}")
            print(f"   Documents: {len(self.test_data_ids['documents'])}")
            print(f"   Requirements: {len(self.test_data_ids['requirements'])}")
            print(f"   Tests: {len(self.test_data_ids['tests'])}")

        except Exception as e:
            error_msg = f"Failed to setup test data: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.test_results["errors"].append({
                "phase": "setup",
                "error": error_msg
            })
            raise

    async def call_mcp_query_tool(
        self,
        query_type: str,
        entities: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Call the MCP query tool directly."""
        try:
            from tools.query import data_query

            result = await data_query(
                auth_token=self.auth_token,
                query_type=query_type,
                entities=entities,
                **kwargs
            )
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query_type": query_type,
                "entities": entities
            }

    async def test_search_query(self):
        """Test SEARCH query type with various parameters."""
        print("\n🔍 Testing SEARCH query type...")
        test_name = "search"
        self.test_results["query_types_tested"].append(test_name)
        results = []

        test_cases = [
            {
                "name": "search_authentication_all_entities",
                "description": "Search for 'authentication' across all entity types",
                "entities": ["project", "document", "requirement"],
                "search_term": "authentication",
                "limit": 10
            },
            {
                "name": "search_oauth_high_priority",
                "description": "Search 'OAuth' in high priority requirements only",
                "entities": ["requirement"],
                "search_term": "OAuth",
                "conditions": {"priority": "high"},
                "limit": 5
            },
            {
                "name": "search_semantic_vector",
                "description": "Search for 'semantic' and 'vector' terms across documents and requirements",
                "entities": ["document", "requirement"],
                "search_term": "semantic vector",
                "limit": 10
            },
            {
                "name": "search_distributed_training",
                "description": "Search for distributed training across all entities",
                "entities": ["project", "requirement", "test"],
                "search_term": "distributed",
                "limit": 15
            },
            {
                "name": "search_embedding_approved_only",
                "description": "Search for 'embedding' in approved requirements",
                "entities": ["requirement"],
                "search_term": "embedding",
                "conditions": {"status": "approved"},
                "limit": 5
            }
        ]

        for test_case in test_cases:
            print(f"  Running: {test_case['name']}...")
            start_time = time.time()

            try:
                mcp_result = await self.call_mcp_query_tool(
                    query_type="search",
                    entities=test_case["entities"],
                    search_term=test_case["search_term"],
                    conditions=test_case.get("conditions"),
                    limit=test_case.get("limit")
                )

                execution_time = (time.time() - start_time) * 1000

                result = {
                    "success": "error" not in mcp_result,
                    "test_case": test_case["name"],
                    "search_term": test_case["search_term"],
                    "entities_searched": test_case["entities"],
                    "execution_time_ms": execution_time,
                    "total_results": mcp_result.get("total_results", 0),
                    "results_summary": {
                        entity: data.get("count", 0)
                        for entity, data in mcp_result.get("results_by_entity", {}).items()
                    } if "results_by_entity" in mcp_result else {},
                    "error": mcp_result.get("error")
                }

                results.append(result)

                if result["success"]:
                    print(f"    ✅ Completed in {execution_time:.2f}ms - Found {result['total_results']} results")
                else:
                    print(f"    ❌ Failed: {result['error']}")

            except Exception as e:
                error_result = {
                    "success": False,
                    "test_case": test_case["name"],
                    "error": str(e),
                    "execution_time_ms": (time.time() - start_time) * 1000
                }
                results.append(error_result)
                print(f"    ❌ Failed: {str(e)}")

        self.test_results["test_results"][test_name] = results
        return results

    async def test_aggregate_query(self):
        """Test AGGREGATE query type."""
        print("\n📊 Testing AGGREGATE query type...")
        test_name = "aggregate"
        self.test_results["query_types_tested"].append(test_name)
        results = []

        test_cases = [
            {
                "name": "aggregate_all_entities",
                "description": "Get summary statistics for all entity types",
                "entities": ["organization", "project", "document", "requirement", "test"]
            },
            {
                "name": "aggregate_active_projects",
                "description": "Aggregate active projects only",
                "entities": ["project"],
                "conditions": {"status": "active"}
            },
            {
                "name": "aggregate_high_priority_requirements",
                "description": "Count high priority requirements with status breakdown",
                "entities": ["requirement"],
                "conditions": {"priority": "high"}
            },
            {
                "name": "aggregate_passed_tests",
                "description": "Aggregate passed tests only",
                "entities": ["test"],
                "conditions": {"status": "passed"}
            },
            {
                "name": "aggregate_multi_entity_filtered",
                "description": "Aggregate projects and requirements with filters",
                "entities": ["project", "requirement"],
                "conditions": {"status": "approved"}
            }
        ]

        for test_case in test_cases:
            print(f"  Running: {test_case['name']}...")
            start_time = time.time()

            try:
                mcp_result = await self.call_mcp_query_tool(
                    query_type="aggregate",
                    entities=test_case["entities"],
                    conditions=test_case.get("conditions")
                )

                execution_time = (time.time() - start_time) * 1000

                result = {
                    "success": "error" not in mcp_result,
                    "test_case": test_case["name"],
                    "aggregation_type": "summary_stats",
                    "entities_analyzed": test_case["entities"],
                    "execution_time_ms": execution_time,
                    "results_summary": {
                        entity: {
                            "total": data.get("total_count", 0),
                            "recent": data.get("recent_count", 0),
                            "has_status_breakdown": bool(data.get("status_breakdown"))
                        }
                        for entity, data in mcp_result.get("results", {}).items()
                    } if "results" in mcp_result else {},
                    "error": mcp_result.get("error")
                }

                results.append(result)

                if result["success"]:
                    print(f"    ✅ Completed in {execution_time:.2f}ms")
                else:
                    print(f"    ❌ Failed: {result['error']}")

            except Exception as e:
                error_result = {
                    "success": False,
                    "test_case": test_case["name"],
                    "error": str(e),
                    "execution_time_ms": (time.time() - start_time) * 1000
                }
                results.append(error_result)
                print(f"    ❌ Failed: {str(e)}")

        self.test_results["test_results"][test_name] = results
        return results

    async def test_analyze_query(self):
        """Test ANALYZE query type."""
        print("\n🔬 Testing ANALYZE query type...")
        test_name = "analyze"
        self.test_results["query_types_tested"].append(test_name)
        results = []

        test_cases = [
            {
                "name": "analyze_organizations",
                "description": "Deep analysis of organizations with members and projects",
                "entities": ["organization"]
            },
            {
                "name": "analyze_projects",
                "description": "Analyze project complexity and document distribution",
                "entities": ["project"]
            },
            {
                "name": "analyze_requirements",
                "description": "Analyze requirement status, priority, and test coverage",
                "entities": ["requirement"]
            },
            {
                "name": "analyze_active_projects_only",
                "description": "Analyze only active projects",
                "entities": ["project"],
                "conditions": {"status": "active"}
            },
            {
                "name": "analyze_multi_entity",
                "description": "Analyze organizations and projects together",
                "entities": ["organization", "project"]
            }
        ]

        for test_case in test_cases:
            print(f"  Running: {test_case['name']}...")
            start_time = time.time()

            try:
                mcp_result = await self.call_mcp_query_tool(
                    query_type="analyze",
                    entities=test_case["entities"],
                    conditions=test_case.get("conditions")
                )

                execution_time = (time.time() - start_time) * 1000

                result = {
                    "success": "error" not in mcp_result,
                    "test_case": test_case["name"],
                    "analysis_type": "deep_analysis",
                    "entities_analyzed": test_case["entities"],
                    "execution_time_ms": execution_time,
                    "analysis_summary": {
                        entity: {
                            k: v for k, v in data.items()
                            if k != "error" and not isinstance(v, (dict, list))
                        }
                        for entity, data in mcp_result.get("analysis", {}).items()
                    } if "analysis" in mcp_result else {},
                    "error": mcp_result.get("error")
                }

                results.append(result)

                if result["success"]:
                    print(f"    ✅ Completed in {execution_time:.2f}ms")
                else:
                    print(f"    ❌ Failed: {result['error']}")

            except Exception as e:
                error_result = {
                    "success": False,
                    "test_case": test_case["name"],
                    "error": str(e),
                    "execution_time_ms": (time.time() - start_time) * 1000
                }
                results.append(error_result)
                print(f"    ❌ Failed: {str(e)}")

        self.test_results["test_results"][test_name] = results
        return results

    async def test_relationships_query(self):
        """Test RELATIONSHIPS query type."""
        print("\n🔗 Testing RELATIONSHIPS query type...")
        test_name = "relationships"
        self.test_results["query_types_tested"].append(test_name)
        results = []

        test_cases = [
            {
                "name": "all_relationships",
                "description": "Analyze all relationship types across all entities",
                "entities": ["organization", "project", "requirement", "test"]
            },
            {
                "name": "test_coverage_relationships",
                "description": "Analyze requirement-test coverage relationships",
                "entities": ["requirement", "test"],
                "conditions": {"relationship_type": "tests"}
            },
            {
                "name": "project_relationships",
                "description": "Analyze project-specific relationships",
                "entities": ["project"]
            }
        ]

        for test_case in test_cases:
            print(f"  Running: {test_case['name']}...")
            start_time = time.time()

            try:
                mcp_result = await self.call_mcp_query_tool(
                    query_type="relationships",
                    entities=test_case["entities"],
                    conditions=test_case.get("conditions")
                )

                execution_time = (time.time() - start_time) * 1000

                result = {
                    "success": "error" not in mcp_result,
                    "test_case": test_case["name"],
                    "query_type": "relationship_analysis",
                    "execution_time_ms": execution_time,
                    "relationships_found": {
                        rel_type: data.get("total_count", 0)
                        for rel_type, data in mcp_result.get("relationships", {}).items()
                    } if "relationships" in mcp_result else {},
                    "error": mcp_result.get("error")
                }

                results.append(result)

                if result["success"]:
                    total_rels = sum(result["relationships_found"].values())
                    print(f"    ✅ Completed in {execution_time:.2f}ms - Found {total_rels} total relationships")
                else:
                    print(f"    ❌ Failed: {result['error']}")

            except Exception as e:
                error_result = {
                    "success": False,
                    "test_case": test_case["name"],
                    "error": str(e),
                    "execution_time_ms": (time.time() - start_time) * 1000
                }
                results.append(error_result)
                print(f"    ❌ Failed: {str(e)}")

        self.test_results["test_results"][test_name] = results
        return results

    async def test_rag_search_query(self):
        """Test RAG_SEARCH with all modes."""
        print("\n🤖 Testing RAG_SEARCH query type (all modes)...")
        test_name = "rag_search"
        self.test_results["query_types_tested"].append(test_name)
        results = []

        # Test all RAG modes with different queries
        test_cases = [
            # AUTO mode tests
            {
                "mode": "auto",
                "name": "rag_auto_short_query",
                "search_term": "OAuth2 tokens",
                "entities": ["requirement", "document"],
                "similarity_threshold": 0.7,
                "limit": 5,
                "description": "Auto mode with short query (should use keyword)"
            },
            {
                "mode": "auto",
                "name": "rag_auto_long_query",
                "search_term": "user authentication with OAuth2 tokens and session management",
                "entities": ["requirement", "document"],
                "similarity_threshold": 0.7,
                "limit": 10,
                "description": "Auto mode with long query (should use semantic)"
            },
            # SEMANTIC mode tests
            {
                "mode": "semantic",
                "name": "rag_semantic_auth_flow",
                "search_term": "secure user login with password encryption and session tokens",
                "entities": ["requirement"],
                "similarity_threshold": 0.7,
                "limit": 5,
                "description": "Semantic search for authentication concepts"
            },
            {
                "mode": "semantic",
                "name": "rag_semantic_vector_search",
                "search_term": "embedding-based similarity matching with vector representations",
                "entities": ["requirement", "document"],
                "similarity_threshold": 0.75,
                "limit": 5,
                "description": "Semantic search for vector/embedding concepts"
            },
            {
                "mode": "semantic",
                "name": "rag_semantic_ml_training",
                "search_term": "distributed machine learning with GPU acceleration",
                "entities": ["requirement", "project"],
                "similarity_threshold": 0.6,
                "limit": 8,
                "description": "Semantic search for ML training concepts"
            },
            # KEYWORD mode tests
            {
                "mode": "keyword",
                "name": "rag_keyword_pkce",
                "search_term": "PKCE",
                "entities": ["requirement"],
                "similarity_threshold": 0.7,
                "limit": 5,
                "description": "Keyword search for specific term PKCE"
            },
            {
                "mode": "keyword",
                "name": "rag_keyword_jwt",
                "search_term": "JWT token",
                "entities": ["requirement", "document"],
                "similarity_threshold": 0.7,
                "limit": 5,
                "description": "Keyword search for JWT tokens"
            },
            # HYBRID mode tests
            {
                "mode": "hybrid",
                "name": "rag_hybrid_search_engine",
                "search_term": "search algorithm with embeddings and keyword matching",
                "entities": ["requirement", "document", "project"],
                "similarity_threshold": 0.7,
                "limit": 10,
                "description": "Hybrid search combining semantic and keyword"
            },
            {
                "mode": "hybrid",
                "name": "rag_hybrid_security",
                "search_term": "authentication security with token management",
                "entities": ["requirement"],
                "similarity_threshold": 0.65,
                "limit": 10,
                "description": "Hybrid search for security concepts"
            },
            {
                "mode": "hybrid",
                "name": "rag_hybrid_performance",
                "search_term": "response time optimization",
                "entities": ["requirement"],
                "similarity_threshold": 0.7,
                "limit": 5,
                "description": "Hybrid search for performance requirements"
            },
            # Different threshold tests
            {
                "mode": "semantic",
                "name": "rag_semantic_high_threshold",
                "search_term": "OAuth2 authorization code flow",
                "entities": ["requirement"],
                "similarity_threshold": 0.85,
                "limit": 3,
                "description": "Semantic search with high similarity threshold"
            },
            {
                "mode": "semantic",
                "name": "rag_semantic_low_threshold",
                "search_term": "search functionality",
                "entities": ["requirement", "document"],
                "similarity_threshold": 0.5,
                "limit": 15,
                "description": "Semantic search with low similarity threshold"
            }
        ]

        for test_case in test_cases:
            print(f"  Running: {test_case['name']} ({test_case['mode']} mode)...")
            start_time = time.time()

            try:
                mcp_result = await self.call_mcp_query_tool(
                    query_type="rag_search",
                    entities=test_case["entities"],
                    search_term=test_case["search_term"],
                    rag_mode=test_case["mode"],
                    similarity_threshold=test_case["similarity_threshold"],
                    limit=test_case["limit"]
                )

                execution_time = (time.time() - start_time) * 1000

                result = {
                    "success": "error" not in mcp_result,
                    "test_case": test_case["name"],
                    "search_type": "rag_search",
                    "mode": test_case["mode"],
                    "actual_mode_used": mcp_result.get("mode"),
                    "query": test_case["search_term"],
                    "similarity_threshold": test_case["similarity_threshold"],
                    "execution_time_ms": execution_time,
                    "total_results": mcp_result.get("total_results", 0),
                    "query_embedding_tokens": mcp_result.get("query_embedding_tokens"),
                    "search_time_ms": mcp_result.get("search_time_ms"),
                    "error": mcp_result.get("error"),
                    "description": test_case["description"]
                }

                results.append(result)

                if result["success"]:
                    print(f"    ✅ Completed in {execution_time:.2f}ms - Found {result['total_results']} results (mode: {result['actual_mode_used']})")
                else:
                    print(f"    ❌ Failed: {result['error']}")

            except Exception as e:
                error_result = {
                    "success": False,
                    "test_case": test_case["name"],
                    "mode": test_case["mode"],
                    "error": str(e),
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "description": test_case["description"]
                }
                results.append(error_result)
                print(f"    ❌ Failed: {str(e)}")

        self.test_results["test_results"][test_name] = results
        return results

    async def test_similarity_query(self):
        """Test SIMILARITY query type."""
        print("\n🔍 Testing SIMILARITY query type...")
        test_name = "similarity"
        self.test_results["query_types_tested"].append(test_name)
        results = []

        test_cases = [
            {
                "name": "similar_auth_requirements",
                "description": "Find requirements similar to authentication text",
                "content": "System must implement secure user login with password encryption and session tokens for maintaining user state",
                "entity_type": "requirement",
                "similarity_threshold": 0.7,
                "limit": 5
            },
            {
                "name": "similar_search_documents",
                "description": "Find documents similar to search algorithm description",
                "content": "Implementing vector search with embeddings for semantic similarity matching and hybrid retrieval combining keyword and vector approaches",
                "entity_type": "document",
                "similarity_threshold": 0.75,
                "limit": 3
            },
            {
                "name": "similar_ml_requirements",
                "description": "Find requirements similar to ML training description",
                "content": "Distributed training infrastructure with GPU acceleration for deep learning models and neural networks",
                "entity_type": "requirement",
                "similarity_threshold": 0.65,
                "limit": 5
            },
            {
                "name": "similar_performance_requirements",
                "description": "Find requirements similar to performance specs",
                "content": "Low latency response times with sub-second query execution and efficient caching mechanisms",
                "entity_type": "requirement",
                "similarity_threshold": 0.6,
                "limit": 5
            },
            {
                "name": "similar_security_requirements_high_threshold",
                "description": "Find very similar security requirements",
                "content": "OAuth2 authorization with PKCE extension for preventing authorization code interception attacks",
                "entity_type": "requirement",
                "similarity_threshold": 0.85,
                "limit": 3
            },
            {
                "name": "similar_projects",
                "description": "Find projects similar to analytics description",
                "content": "Real-time data visualization with interactive dashboards and streaming analytics processing",
                "entity_type": "project",
                "similarity_threshold": 0.7,
                "limit": 3
            }
        ]

        for test_case in test_cases:
            print(f"  Running: {test_case['name']}...")
            start_time = time.time()

            try:
                mcp_result = await self.call_mcp_query_tool(
                    query_type="similarity",
                    entities=[test_case["entity_type"]],  # Wrap in array
                    content=test_case["content"],
                    entity_type=test_case["entity_type"],
                    similarity_threshold=test_case["similarity_threshold"],
                    limit=test_case["limit"]
                )

                execution_time = (time.time() - start_time) * 1000

                result = {
                    "success": "error" not in mcp_result,
                    "test_case": test_case["name"],
                    "analysis_type": "similarity_analysis",
                    "entity_type": test_case["entity_type"],
                    "source_content_preview": test_case["content"][:100] + "...",
                    "similarity_threshold": test_case["similarity_threshold"],
                    "execution_time_ms": execution_time,
                    "total_results": mcp_result.get("total_results", 0),
                    "query_embedding_tokens": mcp_result.get("query_embedding_tokens"),
                    "search_time_ms": mcp_result.get("search_time_ms"),
                    "error": mcp_result.get("error"),
                    "description": test_case["description"]
                }

                results.append(result)

                if result["success"]:
                    print(f"    ✅ Completed in {execution_time:.2f}ms - Found {result['total_results']} similar items")
                else:
                    print(f"    ❌ Failed: {result['error']}")

            except Exception as e:
                error_result = {
                    "success": False,
                    "test_case": test_case["name"],
                    "error": str(e),
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "description": test_case["description"]
                }
                results.append(error_result)
                print(f"    ❌ Failed: {str(e)}")

        self.test_results["test_results"][test_name] = results
        return results

    async def cleanup_test_data(self):
        """Clean up all test data."""
        print("\n🧹 Cleaning up test data...")

        try:
            # Delete in reverse order of dependencies
            cleanup_order = [
                ("requirement_tests", "test-requirement relationships"),
                ("tests", "tests"),
                ("requirements", "requirements"),
                ("documents", "documents"),
                ("project_members", "project members"),
                ("projects", "projects"),
                ("organization_members", "organization members"),
                ("organizations", "organizations")
            ]

            for table, description in cleanup_order:
                if table in ["organization_members"]:
                    # organization_members has created_by
                    if self.test_data_ids.get("organizations"):
                        for org_id in self.test_data_ids["organizations"]:
                            self.supabase.table(table).delete().eq("organization_id", org_id).execute()
                        print(f"  ✅ Deleted {description}")
                elif table == "project_members":
                    # project_members - delete by project_id
                    if self.test_data_ids.get("projects"):
                        try:
                            for proj_id in self.test_data_ids["projects"]:
                                self.supabase.table(table).delete().eq("project_id", proj_id).execute()
                            print(f"  ✅ Deleted {description}")
                        except Exception as e:
                            if "permission denied" not in str(e):
                                raise
                            # Skip if permission denied (might be handled by cascade)
                elif table == "requirement_tests":
                    # requirement_tests doesn't have created_by, delete all from our test requirements
                    if self.test_data_ids.get("requirements"):
                        for req_id in self.test_data_ids["requirements"]:
                            self.supabase.table(table).delete().eq("requirement_id", req_id).execute()
                        print(f"  ✅ Deleted {description}")
                elif table == "organizations":
                    # Delete organizations
                    for org_id in self.test_data_ids.get("organizations", []):
                        self.supabase.table(table).delete().eq("id", org_id).execute()
                    print(f"  ✅ Deleted {len(self.test_data_ids.get('organizations', []))} organizations")
                elif table == "projects":
                    for proj_id in self.test_data_ids.get("projects", []):
                        self.supabase.table(table).delete().eq("id", proj_id).execute()
                    print(f"  ✅ Deleted {len(self.test_data_ids.get('projects', []))} projects")
                else:
                    # For other tables, use stored IDs
                    entity_key = table
                    if table == "tests":
                        entity_key = "tests"

                    for entity_id in self.test_data_ids.get(entity_key, []):
                        self.supabase.table(table).delete().eq("id", entity_id).execute()

                    if self.test_data_ids.get(entity_key):
                        print(f"  ✅ Deleted {len(self.test_data_ids[entity_key])} {description}")

            print("\n✅ Cleanup complete!")

        except Exception as e:
            error_msg = f"Failed to cleanup test data: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.test_results["errors"].append({
                "phase": "cleanup",
                "error": error_msg
            })

    async def run_all_tests(self):
        """Run all query tool tests."""
        print("=" * 80)
        print("🧪 COMPREHENSIVE MCP QUERY TOOL TEST SUITE")
        print("=" * 80)

        try:
            # Initialize
            await self.initialize_auth()

            # Cleanup any existing test data first
            await self.cleanup_existing_test_data()

            # Setup
            await self.setup_test_data()

            # Run all query type tests
            await self.test_search_query()
            await self.test_aggregate_query()
            await self.test_analyze_query()
            await self.test_relationships_query()
            await self.test_rag_search_query()
            await self.test_similarity_query()

            # Generate summary
            total_tests = sum(len(results) for results in self.test_results["test_results"].values())
            successful_tests = sum(
                sum(1 for r in results if r.get("success", False))
                for results in self.test_results["test_results"].values()
            )
            failed_tests = total_tests - successful_tests

            self.test_results["summary"] = {
                "total_query_types_tested": len(self.test_results["query_types_tested"]),
                "query_types": self.test_results["query_types_tested"],
                "total_test_cases": total_tests,
                "successful_test_cases": successful_tests,
                "failed_test_cases": failed_tests,
                "success_rate": f"{(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%",
                "total_errors": len(self.test_results["errors"]),
                "test_data_created": self.test_results["test_data_created"]
            }

        finally:
            # Always cleanup
            await self.cleanup_test_data()

        # Save results
        self.save_results()

        return self.test_results

    def save_results(self):
        """Save test results to JSON file."""
        output_file = "mcp_query_tool_test_results.json"

        with open(output_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)

        print(f"\n📊 Test results saved to: {output_file}")
        print(f"\n{'=' * 80}")
        print("📈 TEST SUMMARY")
        print(f"{'=' * 80}")
        print(f"Query Types Tested: {self.test_results['summary']['total_query_types_tested']}")
        print(f"  - {', '.join(self.test_results['summary']['query_types'])}")
        print(f"\nTotal Test Cases: {self.test_results['summary']['total_test_cases']}")
        print(f"  ✅ Successful: {self.test_results['summary']['successful_test_cases']}")
        print(f"  ❌ Failed: {self.test_results['summary']['failed_test_cases']}")
        print(f"  Success Rate: {self.test_results['summary']['success_rate']}")

        print("\n📁 Test Data Created:")
        for entity_type, count in self.test_results['test_data_created'].items():
            print(f"  - {entity_type}: {count}")

        if self.test_results["errors"]:
            print("\n❌ Errors Encountered:")
            for error in self.test_results["errors"]:
                print(f"  - [{error['phase']}] {error['error']}")

        # Print detailed results per query type
        print(f"\n{'=' * 80}")
        print("📋 DETAILED RESULTS BY QUERY TYPE")
        print(f"{'=' * 80}")

        for query_type, results in self.test_results["test_results"].items():
            successful = sum(1 for r in results if r.get("success", False))
            total = len(results)
            print(f"\n{query_type.upper()}: {successful}/{total} passed")

            for result in results:
                status = "✅" if result.get("success") else "❌"
                test_name = result.get("test_case", "unknown")
                exec_time = result.get("execution_time_ms", 0)

                if result.get("success"):
                    extra_info = ""
                    if "total_results" in result:
                        extra_info = f" ({result['total_results']} results)"
                    elif "mode" in result and "actual_mode_used" in result:
                        extra_info = f" (mode: {result['actual_mode_used']})"
                    print(f"  {status} {test_name} - {exec_time:.2f}ms{extra_info}")
                else:
                    error = result.get("error", "unknown error")
                    print(f"  {status} {test_name} - {error}")

        print(f"\n{'=' * 80}\n")


async def main():
    """Main entry point."""
    tester = MCPQueryToolTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
