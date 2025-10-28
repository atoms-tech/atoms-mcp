"""
Schemas convenience package.

This module re-exports:
1. Generated models/enums from `schemas.generated.fastapi.schema_public_latest`
2. Application-level constants/enums
3. RLS validators and trigger emulators

The generated exports are built dynamically so new tables/enums automatically
become available without hand-editing this file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from schemas.constants import (
    ENTITY_TABLE_MAP,
    TABLES_WITHOUT_AUDIT_FIELDS,
    TABLES_WITHOUT_SOFT_DELETE,
    Fields,
    Tables,
)
from schemas.enums import (
    EntityStatus,
    EntityType,
    OrganizationType,
    Priority,
    QueryType,
    RAGMode,
    RelationshipType,
)
from schemas.generated.fastapi import schema_public_latest as generated_schema
from schemas.rls import (
    DocumentPolicy,
    OrganizationMemberPolicy,
    OrganizationPolicy,
    PermissionDeniedError,
    PolicyValidator,
    ProfilePolicy,
    ProjectMemberPolicy,
    ProjectPolicy,
    RequirementPolicy,
    TestPolicy,
)
from schemas.triggers import TriggerEmulator

if TYPE_CHECKING:
    from collections.abc import Iterable

GeneratedNames = list[str]


def _unique(seq: Iterable[str]) -> list[str]:
    """Preserve order while removing duplicates."""
    seen: set[str] = set()
    ordered: list[str] = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _export_from_generated(source_name: str, alias: str | None = None) -> str:
    """Attach `source_name` from generated schemas to this module."""
    export_name = alias or source_name
    globals()[export_name] = getattr(generated_schema, source_name)
    return export_name


def _build_direct_model_exports() -> GeneratedNames:
    """Explicit models we want to re-export verbatim."""
    model_names = [
        "BlockBaseSchema",  # used for block transform helpers
        "Document",
        "DocumentInsert",
        "DocumentUpdate",
        "Organization",
        "OrganizationInsert",
        "OrganizationUpdate",
        "Project",
        "ProjectInsert",
        "ProjectUpdate",
        "Requirement",
        "RequirementInsert",
        "RequirementUpdate",
    ]
    exports: list[str] = []
    for name in model_names:
        exports.append(_export_from_generated(name))
    return exports


def _build_enum_exports() -> tuple[GeneratedNames, GeneratedNames]:
    """Export Public*Enum classes and alias them without the prefix where safe."""
    enum_exports: list[str] = []
    alias_exports: list[str] = []
    for name in sorted(dir(generated_schema)):
        if not (name.startswith("Public") and name.endswith("Enum")):
            continue

        enum_exports.append(_export_from_generated(name))

        alias = name.removeprefix("Public").removesuffix("Enum")
        if not alias or alias in globals():
            continue

        alias_exports.append(_export_from_generated(name, alias=alias))

    return enum_exports, alias_exports


def _build_row_exports() -> GeneratedNames:
    """Alias *BaseSchema classes to *Row for ergonomic DB usage."""
    row_exports: list[str] = []
    for name in sorted(dir(generated_schema)):
        if not name.endswith("BaseSchema"):
            continue
        alias = name.removesuffix("BaseSchema") + "Row"
        if alias in globals():
            continue
        row_exports.append(_export_from_generated(name, alias=alias))
    return row_exports


DIRECT_MODEL_EXPORTS = _build_direct_model_exports()
ENUM_EXPORTS, ENUM_ALIAS_EXPORTS = _build_enum_exports()
ROW_EXPORTS = _build_row_exports()

MANUAL_EXPORTS = [
    "ENTITY_TABLE_MAP",
    "TABLES_WITHOUT_AUDIT_FIELDS",
    "TABLES_WITHOUT_SOFT_DELETE",
    "DocumentPolicy",
    "EntityStatus",
    "EntityType",
    "Fields",
    "OrganizationMemberPolicy",
    "OrganizationPolicy",
    "OrganizationType",
    "PermissionDeniedError",
    "PolicyValidator",
    "Priority",
    "ProfilePolicy",
    "ProjectMemberPolicy",
    "ProjectPolicy",
    "QueryType",
    "RAGMode",
    "RelationshipType",
    "RequirementPolicy",
    "Tables",
    "TestPolicy",
    "TriggerEmulator",
]

__all__ = _unique(
    MANUAL_EXPORTS
    + DIRECT_MODEL_EXPORTS
    + ENUM_EXPORTS
    + ENUM_ALIAS_EXPORTS
    + ROW_EXPORTS
)
