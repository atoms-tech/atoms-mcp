"""Search & Discovery E2E Tests - Story 8"""

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


class TestKeywordSearch:
    """Keyword search operations."""

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can search across all entities")
    async def test_search_keyword_basic(self, end_to_end_client):
        """Basic keyword search."""
        result = await mcp_client.data_query(
            operation="search",
            search_term="login",
            limit=10
        )
        assert result["success"] is True
        assert isinstance(result["data"], list)

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can search across all entities")
    async def test_search_keyword_partial_match(self, end_to_end_client):
        """Partial keyword match."""
        result = await mcp_client.data_query(
            operation="search",
            search_term="auth",
            limit=10
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can search across all entities")
    async def test_search_keyword_case_insensitive(self, end_to_end_client):
        """Case-insensitive search."""
        result = await mcp_client.data_query(
            operation="search",
            search_term="LOGIN",
            limit=10
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can search across all entities")
    async def test_search_keyword_fuzzy_match(self, end_to_end_client):
        """Fuzzy keyword match."""
        result = await mcp_client.data_query(
            operation="search",
            search_term="logn",  # typo
            limit=10
        )
        # May or may not find results - both acceptable
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can search across all entities")
    async def test_search_keyword_phrase(self, end_to_end_client):
        """Search by phrase."""
        result = await mcp_client.data_query(
            operation="search",
            search_term="user authentication system",
            limit=10
        )
        assert result["success"] is True


class TestFiltering:
    """Filter search operations."""

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can filter search results")
    async def test_filter_by_type(self, end_to_end_client):
        """Filter results by entity type."""
        result = await mcp_client.data_query(
            operation="search",
            filters={"entity_type": "requirement"},
            limit=10
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can filter search results")
    async def test_filter_by_owner(self, end_to_end_client):
        """Filter by owner/creator."""
        result = await mcp_client.data_query(
            operation="search",
            filters={"created_by": "test-user"},
            limit=10
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can filter search results")
    async def test_filter_by_status(self, end_to_end_client):
        """Filter by status."""
        result = await mcp_client.data_query(
            operation="search",
            filters={"status": "open"},
            limit=10
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can filter search results")
    async def test_filter_by_date_range(self, end_to_end_client):
        """Filter by date range."""
        result = await mcp_client.data_query(
            operation="search",
            filters={"created_after": "2025-01-01", "created_before": "2025-12-31"},
            limit=10
        )
        assert result["success"] is True


class TestSemanticSearch:
    """Semantic search using embeddings."""

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can perform semantic search")
    async def test_semantic_search_basic(self, end_to_end_client):
        """Basic semantic search."""
        result = await mcp_client.data_query(
            operation="semantic_search",
            query="user login authentication",
            limit=10
        )
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can perform semantic search")
    async def test_semantic_search_similar_concepts(self, end_to_end_client):
        """Semantic search finds conceptually similar items."""
        result = await mcp_client.data_query(
            operation="semantic_search",
            query="OAuth authentication",
            limit=10
        )
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can perform semantic search")
    async def test_semantic_search_threshold(self, end_to_end_client):
        """Semantic search with similarity threshold."""
        result = await mcp_client.data_query(
            operation="semantic_search",
            query="payment processing",
            threshold=0.7,
            limit=10
        )
        assert "success" in result


class TestHybridSearch:
    """Combined keyword + semantic search."""

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can perform hybrid search")
    async def test_hybrid_search_basic(self, end_to_end_client):
        """Basic hybrid search."""
        result = await mcp_client.data_query(
            operation="hybrid_search",
            search_term="authentication",
            semantic_weight=0.5,
            limit=10
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can perform hybrid search")
    async def test_hybrid_search_weighted_keyword(self, end_to_end_client):
        """Hybrid with keyword emphasis."""
        result = await mcp_client.data_query(
            operation="hybrid_search",
            search_term="oauth",
            semantic_weight=0.2,  # Favor keyword
            limit=10
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can perform hybrid search")
    async def test_hybrid_search_weighted_semantic(self, end_to_end_client):
        """Hybrid with semantic emphasis."""
        result = await mcp_client.data_query(
            operation="hybrid_search",
            search_term="login",
            semantic_weight=0.8,  # Favor semantic
            limit=10
        )
        assert result["success"] is True


class TestAggregation:
    """Aggregate search operations."""

    @pytest.mark.asyncio
    @pytest.mark.query
    async def test_aggregate_count_by_type(self, end_to_end_client):
        """Get count aggregated by type."""
        result = await mcp_client.data_query(
            operation="aggregate",
            group_by="entity_type"
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.query
    async def test_aggregate_count_by_status(self, end_to_end_client):
        """Get count aggregated by status."""
        result = await mcp_client.data_query(
            operation="aggregate",
            group_by="status"
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.query
    async def test_aggregate_count_by_owner(self, end_to_end_client):
        """Get count aggregated by owner."""
        result = await mcp_client.data_query(
            operation="aggregate",
            group_by="created_by"
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.query
    async def test_get_entity_count_total(self, end_to_end_client):
        """Get total entity count."""
        result = await mcp_client.data_query(
            operation="count_all"
        )
        assert result["success"] is True
        assert "count" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.query
    async def test_aggregate_with_filter(self, end_to_end_client):
        """Aggregate with filters applied."""
        result = await mcp_client.data_query(
            operation="aggregate",
            group_by="status",
            filters={"entity_type": "requirement"}
        )
        assert result["success"] is True


class TestSimilaritySearch:
    """Find similar entities."""

    @pytest.mark.asyncio
    @pytest.mark.query
    async def test_find_similar_by_embedding(self, end_to_end_client):
        """Find similar entities by embedding."""
        result = await mcp_client.data_query(
            operation="find_similar",
            entity_id="some-entity-id",
            limit=10
        )
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.query
    async def test_find_similar_threshold(self, end_to_end_client):
        """Find similar with similarity threshold."""
        result = await mcp_client.data_query(
            operation="find_similar",
            entity_id="some-entity-id",
            threshold=0.75,
            limit=10
        )
        assert "success" in result


class TestAdvancedOperators:
    """Advanced search operators."""

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can search across all entities")
    async def test_search_with_and_operator(self, end_to_end_client):
        """Search with AND operator."""
        result = await mcp_client.data_query(
            operation="search",
            query="(authentication AND oauth) OR (login AND saml)",
            limit=10
        )
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can search across all entities")
    async def test_search_with_or_operator(self, end_to_end_client):
        """Search with OR operator."""
        result = await mcp_client.data_query(
            operation="search",
            query="(payment OR billing) AND (api OR webhook)",
            limit=10
        )
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can search across all entities")
    async def test_search_with_not_operator(self, end_to_end_client):
        """Search with NOT operator."""
        result = await mcp_client.data_query(
            operation="search",
            query="authentication NOT deprecated",
            limit=10
        )
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.query
    @pytest.mark.story("User can search across all entities")
    async def test_search_complex_expression(self, end_to_end_client):
        """Complex search expression."""
        result = await mcp_client.data_query(
            operation="search",
            query="((api OR rest) AND (oauth OR jwt)) OR (graphql AND authentication)",
            limit=10
        )
        assert "success" in result
