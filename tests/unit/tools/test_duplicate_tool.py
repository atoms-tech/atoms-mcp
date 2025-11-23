"""Tests for duplicate detection tool."""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


class TestDuplicateDetectionTool:
    """Test duplicate detection tool functionality."""

    @pytest.mark.asyncio
    async def test_duplicate_tool_import(self):
        """Test that duplicate detection tool can be imported."""
        from tools.duplicate_detection import DuplicateDetectionTool
        assert DuplicateDetectionTool is not None

    @pytest.mark.asyncio
    async def test_duplicate_tool_initialization(self):
        """Test duplicate detection tool initialization."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()
        assert tool is not None

    @pytest.mark.asyncio
    async def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        from tools.duplicate_detection import cosine_similarity
        
        # Identical vectors
        sim = cosine_similarity([1, 0], [1, 0])
        assert sim == 1.0
        
        # Orthogonal vectors
        sim = cosine_similarity([1, 0], [0, 1])
        assert sim == 0.0

    @pytest.mark.asyncio
    async def test_cosine_similarity_error(self):
        """Test cosine similarity error handling."""
        from tools.duplicate_detection import cosine_similarity
        
        # Different lengths
        with pytest.raises(ValueError):
            cosine_similarity([1, 0], [1, 0, 1])

    @pytest.mark.asyncio
    async def test_duplicate_tool_detect_duplicates(self):
        """Test detect duplicates method."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()
        
        project_id = str(uuid.uuid4())
        result = await tool.detect_duplicates(
            project_id=project_id,
            similarity_threshold=0.95
        )
        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_duplicate_tool_with_auth(self):
        """Test duplicate detection tool with auth token."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()
        
        project_id = str(uuid.uuid4())
        result = await tool.detect_duplicates(
            project_id=project_id,
            auth_token="test-token"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_tool_low_threshold(self):
        """Test duplicate detection with low threshold."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()
        
        project_id = str(uuid.uuid4())
        result = await tool.detect_duplicates(
            project_id=project_id,
            similarity_threshold=0.5
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_tool_high_threshold(self):
        """Test duplicate detection with high threshold."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()
        
        project_id = str(uuid.uuid4())
        result = await tool.detect_duplicates(
            project_id=project_id,
            similarity_threshold=0.99
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_tool_default_threshold(self):
        """Test duplicate detection with default threshold."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()
        
        project_id = str(uuid.uuid4())
        result = await tool.detect_duplicates(project_id=project_id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_tool_empty_project(self):
        """Test duplicate detection on empty project."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()

        project_id = str(uuid.uuid4())
        result = await tool.detect_duplicates(project_id=project_id)
        # Should return empty list for empty project
        assert isinstance(result, list)


# =====================================================
# PHASE 12 ADDITIONAL DUPLICATE DETECTION TESTS
# =====================================================

class TestDuplicateDetectionPhase12:
    """Phase 12 additional duplicate detection tests."""

    @pytest.mark.asyncio
    async def test_duplicate_detection_with_threshold(self):
        """Test duplicate detection with custom threshold."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()

        result = await tool.detect_duplicates(
            project_id=str(uuid.uuid4()),
            similarity_threshold=0.85
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_detection_batch(self):
        """Test batch duplicate detection."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()

        result = await tool.batch_detect_duplicates(
            project_ids=[str(uuid.uuid4()), str(uuid.uuid4())]
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_merge(self):
        """Test merging duplicates."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()

        result = await tool.merge_duplicates(
            primary_id=str(uuid.uuid4()),
            duplicate_ids=[str(uuid.uuid4())]
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_groups(self):
        """Test getting duplicate groups."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()

        result = await tool.get_duplicate_groups(
            project_id=str(uuid.uuid4())
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_mark_not_duplicate(self):
        """Test marking as not duplicate."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()

        result = await tool.mark_as_not_duplicate(
            entity_id_1=str(uuid.uuid4()),
            entity_id_2=str(uuid.uuid4())
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_statistics(self):
        """Test duplicate statistics."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()

        result = await tool.get_duplicate_statistics(
            project_id=str(uuid.uuid4())
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_report(self):
        """Test duplicate report generation."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()

        result = await tool.generate_duplicate_report(
            project_id=str(uuid.uuid4()),
            format="pdf"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_export(self):
        """Test duplicate export."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()

        result = await tool.export_duplicates(
            project_id=str(uuid.uuid4()),
            format="csv"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_import(self):
        """Test duplicate import."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()

        result = await tool.import_duplicates(
            project_id=str(uuid.uuid4()),
            data=[{"primary_id": str(uuid.uuid4()), "duplicate_ids": []}],
            format="csv"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_duplicate_undo_merge(self):
        """Test undoing duplicate merge."""
        from tools.duplicate_detection import DuplicateDetectionTool
        tool = DuplicateDetectionTool()

        result = await tool.undo_merge(
            merge_id=str(uuid.uuid4())
        )
        assert result is not None

