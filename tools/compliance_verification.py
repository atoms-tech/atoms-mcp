"""
Compliance Verification MCP Tool

Phase 4.2: Compliance Verification
- Verifies requirement compliance using FACT_VERIFICATION task type
- Compares requirements against standard clauses
"""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from .base import ToolBase
    from ..services.embedding_vertex import VertexAIEmbeddingService
except ImportError:
    from tools.base import ToolBase
    from services.embedding_vertex import VertexAIEmbeddingService


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same length")

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


class ComplianceVerificationTool(ToolBase):
    """MCP tool for compliance verification."""

    async def verify_compliance(
        self,
        requirement: str,
        standard: str,
        standard_clauses: List[str],
        auth_token: str | None = None,
    ) -> Dict[str, Any]:
        """Verify requirement compliance using FACT_VERIFICATION task type.

        Args:
            requirement: Requirement text to verify
            standard: Standard name (e.g., "ISO 27001", "SOC 2")
            standard_clauses: List of standard clause texts
            auth_token: Authentication token

        Returns:
            Compliance verification result with confidence and relevant clauses
        """
        if auth_token:
            await self._validate_auth(auth_token)

        # Get embedding service
        embedding_service = VertexAIEmbeddingService()

        # Generate embedding with FACT_VERIFICATION task type
        req_result = await embedding_service.generate_embedding(
            requirement,
            task_type="FACT_VERIFICATION",
            output_dimensionality=3072,
        )
        req_embedding = req_result.embedding

        # Generate embeddings for standard clauses
        clause_embeddings = []
        for clause in standard_clauses:
            result = await embedding_service.generate_embedding(
                clause,
                task_type="FACT_VERIFICATION",
                output_dimensionality=3072,
            )
            clause_embeddings.append(result.embedding)

        # Find most relevant clauses
        similarities = [
            cosine_similarity(req_embedding, clause_emb)
            for clause_emb in clause_embeddings
        ]

        # Determine compliance
        max_similarity = max(similarities) if similarities else 0.0
        compliant = max_similarity >= 0.8

        # Get relevant clauses (similarity >= 0.7)
        relevant_clauses = [
            {
                "clause": standard_clauses[i],
                "similarity": float(similarities[i]),
            }
            for i in range(len(standard_clauses))
            if similarities[i] >= 0.7
        ]

        # Sort by similarity (descending)
        relevant_clauses.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "compliant": compliant,
            "confidence": float(max_similarity),
            "standard": standard,
            "relevant_clauses": relevant_clauses,
            "total_clauses_checked": len(standard_clauses),
        }


# Export tool function for MCP
async def verify_compliance(
    requirement: str,
    standard: str,
    standard_clauses: List[str],
    auth_token: str | None = None,
) -> Dict[str, Any]:
    """MCP tool function for compliance verification."""
    tool = ComplianceVerificationTool()
    return await tool.verify_compliance(requirement, standard, standard_clauses, auth_token)
