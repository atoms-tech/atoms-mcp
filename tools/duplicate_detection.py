"""
Duplicate Detection MCP Tool

Phase 3.2: Duplicate Detection
- Detects duplicate requirements using semantic similarity
- Uses SEMANTIC_SIMILARITY task type for optimal comparison
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


class DuplicateDetectionTool(ToolBase):
    """MCP tool for detecting duplicate requirements."""

    async def detect_duplicates(
        self,
        project_id: str,
        similarity_threshold: float = 0.95,
        auth_token: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Detect duplicate requirements using semantic similarity.

        Uses SEMANTIC_SIMILARITY task type for optimal comparison.

        Args:
            project_id: Project UUID
            similarity_threshold: Minimum similarity (0.0-1.0), default 0.95
            auth_token: Authentication token

        Returns:
            List of duplicate pairs with similarity scores
        """
        if auth_token:
            await self._validate_auth(auth_token)

        # Get all requirements for project
        requirements = await self._db_query(
            "requirements",
            project_id=project_id,
            select="id, description, embedding_vector",
        )

        if not requirements:
            return []

        # Get embedding service
        embedding_service = VertexAIEmbeddingService()

        # Generate embeddings for requirements without them
        requirements_with_embeddings: Dict[str, List[float]] = {}

        for req in requirements:
            req_id = req.get("id")
            description = req.get("description", "")
            embedding_vector = req.get("embedding_vector")

            if embedding_vector and isinstance(embedding_vector, list):
                requirements_with_embeddings[req_id] = embedding_vector
            elif description:
                # Generate embedding with SEMANTIC_SIMILARITY task type
                result = await embedding_service.generate_embedding(
                    description,
                    task_type="SEMANTIC_SIMILARITY",
                    output_dimensionality=3072,
                )
                requirements_with_embeddings[req_id] = result.embedding

        # Find duplicates by comparing all pairs
        duplicates = []
        req_ids = list(requirements_with_embeddings.keys())

        for i in range(len(req_ids)):
            for j in range(i + 1, len(req_ids)):
                req1_id = req_ids[i]
                req2_id = req_ids[j]

                try:
                    similarity = cosine_similarity(
                        requirements_with_embeddings[req1_id],
                        requirements_with_embeddings[req2_id],
                    )

                    if similarity >= similarity_threshold:
                        duplicates.append(
                            {
                                "req1_id": req1_id,
                                "req2_id": req2_id,
                                "similarity": float(similarity),
                                "confidence": (
                                    "high" if similarity >= 0.98
                                    else "medium" if similarity >= 0.95
                                    else "low"
                                ),
                                "recommendation": (
                                    "merge" if similarity >= 0.98
                                    else "review" if similarity >= 0.95
                                    else "ignore"
                                ),
                            }
                        )
                except Exception as e:
                    # Skip if similarity calculation fails
                    continue

        # Sort by similarity (descending)
        duplicates.sort(key=lambda x: x["similarity"], reverse=True)

        return duplicates


# Export tool function for MCP
async def detect_duplicates(
    project_id: str,
    similarity_threshold: float = 0.95,
    auth_token: str | None = None,
) -> List[Dict[str, Any]]:
    """MCP tool function for duplicate detection."""
    tool = DuplicateDetectionTool()
    return await tool.detect_duplicates(project_id, similarity_threshold, auth_token)
