"""
Application layer queries.

Queries represent read operations that retrieve data without modifying state.
Each query returns a QueryResult DTO with pagination support.
"""

from .analytics_queries import (
    ActivityQuery,
    AnalyticsQueryHandler,
    EntityCountQuery,
    WorkspaceStatsQuery,
)
from .entity_queries import (
    CountEntitiesQuery,
    EntityQueryHandler,
    GetEntityQuery,
    ListEntitiesQuery,
    SearchEntitiesQuery,
)
from .relationship_queries import (
    FindPathQuery,
    GetDescendantsQuery,
    GetRelatedEntitiesQuery,
    GetRelationshipsQuery,
    RelationshipQueryHandler,
)

__all__ = [
    # Entity queries
    "GetEntityQuery",
    "ListEntitiesQuery",
    "SearchEntitiesQuery",
    "CountEntitiesQuery",
    "EntityQueryHandler",
    # Relationship queries
    "GetRelationshipsQuery",
    "FindPathQuery",
    "GetRelatedEntitiesQuery",
    "GetDescendantsQuery",
    "RelationshipQueryHandler",
    # Analytics queries
    "EntityCountQuery",
    "WorkspaceStatsQuery",
    "ActivityQuery",
    "AnalyticsQueryHandler",
]
