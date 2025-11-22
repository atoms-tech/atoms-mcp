"""Tests for compliance verification tool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestComplianceVerificationTool:
    """Test compliance verification tool functionality."""

    @pytest.mark.asyncio
    async def test_compliance_tool_import(self):
        """Test that compliance tool can be imported."""
        from tools.compliance_verification import ComplianceVerificationTool
        assert ComplianceVerificationTool is not None

    @pytest.mark.asyncio
    async def test_compliance_tool_initialization(self):
        """Test compliance tool initialization."""
        from tools.compliance_verification import ComplianceVerificationTool
        tool = ComplianceVerificationTool()
        assert tool is not None

    @pytest.mark.asyncio
    async def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        from tools.compliance_verification import cosine_similarity
        
        # Identical vectors
        sim = cosine_similarity([1, 0], [1, 0])
        assert sim == 1.0
        
        # Orthogonal vectors
        sim = cosine_similarity([1, 0], [0, 1])
        assert sim == 0.0

    @pytest.mark.asyncio
    async def test_cosine_similarity_error(self):
        """Test cosine similarity error handling."""
        from tools.compliance_verification import cosine_similarity
        
        # Different lengths
        with pytest.raises(ValueError):
            cosine_similarity([1, 0], [1, 0, 1])

    @pytest.mark.asyncio
    async def test_compliance_tool_verify_compliance(self):
        """Test verify compliance method."""
        from tools.compliance_verification import ComplianceVerificationTool
        tool = ComplianceVerificationTool()
        
        result = await tool.verify_compliance(
            requirement="Test requirement",
            standard="ISO 27001",
            standard_clauses=["Clause 1", "Clause 2"]
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_compliance_tool_with_auth(self):
        """Test compliance tool with auth token."""
        from tools.compliance_verification import ComplianceVerificationTool
        tool = ComplianceVerificationTool()
        
        result = await tool.verify_compliance(
            requirement="Test requirement",
            standard="ISO 27001",
            standard_clauses=["Clause 1"],
            auth_token="test-token"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_compliance_tool_multiple_standards(self):
        """Test compliance tool with multiple standards."""
        from tools.compliance_verification import ComplianceVerificationTool
        tool = ComplianceVerificationTool()
        
        result = await tool.verify_compliance(
            requirement="Test requirement",
            standard="SOC 2",
            standard_clauses=["Clause A", "Clause B", "Clause C"]
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_compliance_tool_empty_clauses(self):
        """Test compliance tool with empty clauses."""
        from tools.compliance_verification import ComplianceVerificationTool
        tool = ComplianceVerificationTool()
        
        result = await tool.verify_compliance(
            requirement="Test requirement",
            standard="ISO 9001",
            standard_clauses=[]
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_compliance_tool_long_requirement(self):
        """Test compliance tool with long requirement text."""
        from tools.compliance_verification import ComplianceVerificationTool
        tool = ComplianceVerificationTool()
        
        long_req = "This is a very long requirement text " * 10
        result = await tool.verify_compliance(
            requirement=long_req,
            standard="ISO 27001",
            standard_clauses=["Clause 1"]
        )
        assert result is not None

