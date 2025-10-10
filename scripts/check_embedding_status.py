#!/usr/bin/env python3
"""Check embedding status across all entities.

This script provides a quick overview of embedding coverage and identifies
entities that need embeddings generated.

Usage:
    python scripts/check_embedding_status.py
    python scripts/check_embedding_status.py --verbose
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(".env", override=True)
load_dotenv(".env.production", override=False)


class EmbeddingStatusChecker:
    """Check embedding status across all entities."""

    ENTITY_TYPES = {
        "organization": "organizations",
        "project": "projects",
        "document": "documents",
        "requirement": "requirements"
    }

    def __init__(self, supabase):
        self.supabase = supabase

    def check_all_status(self, verbose: bool = False) -> dict[str, Any]:
        """Check embedding status for all entity types."""
        results = {}
        total_entities = 0
        total_missing = 0
        total_with_embeddings = 0

        print("\n" + "="*60)
        print("EMBEDDING STATUS REPORT")
        print("="*60)
        print(f"Generated at: {datetime.now().isoformat()}\n")

        for entity_type, table_name in self.ENTITY_TYPES.items():
            status = self._check_entity_status(entity_type, table_name, verbose)
            results[entity_type] = status

            total_entities += status["total"]
            total_missing += status["missing"]
            total_with_embeddings += status["with_embeddings"]

        # Overall summary
        print("\n" + "="*60)
        print("OVERALL SUMMARY")
        print("="*60)
        print(f"Total entities:        {total_entities:,}")
        print(f"With embeddings:       {total_with_embeddings:,} ({self._percentage(total_with_embeddings, total_entities)}%)")
        print(f"Missing embeddings:    {total_missing:,} ({self._percentage(total_missing, total_entities)}%)")

        if total_missing > 0:
            print(f"\n⚠️  {total_missing:,} entities need embeddings")
            print("\nRun backfill: python scripts/backfill_embeddings.py")
        else:
            print("\n✅ All entities have embeddings!")

        return {
            "timestamp": datetime.now().isoformat(),
            "total_entities": total_entities,
            "total_with_embeddings": total_with_embeddings,
            "total_missing": total_missing,
            "coverage_percentage": self._percentage(total_with_embeddings, total_entities),
            "by_entity_type": results
        }

    def _check_entity_status(self, entity_type: str, table_name: str, verbose: bool) -> dict[str, Any]:
        """Check embedding status for a specific entity type."""
        try:
            # Total count
            total_result = self.supabase.table(table_name)\
                .select("id", count="exact")\
                .eq("is_deleted", False)\
                .execute()
            total = total_result.count or 0

            # Count with embeddings
            with_embeddings_result = self.supabase.table(table_name)\
                .select("id", count="exact")\
                .not_.is_("embedding", "null")\
                .eq("is_deleted", False)\
                .execute()
            with_embeddings = with_embeddings_result.count or 0

            # Count missing embeddings
            missing = total - with_embeddings

            # Calculate percentage
            coverage = self._percentage(with_embeddings, total)

            # Print entity status
            print(f"\n{entity_type.upper()}")
            print("-" * 40)
            print(f"Total:             {total:,}")
            print(f"With embeddings:   {with_embeddings:,}")
            print(f"Missing:           {missing:,}")
            print(f"Coverage:          {coverage}%")

            # Verbose: show recent entities without embeddings
            if verbose and missing > 0:
                recent_missing = self.supabase.table(table_name)\
                    .select("id, name, created_at")\
                    .is_("embedding", "null")\
                    .eq("is_deleted", False)\
                    .order("created_at", desc=True)\
                    .limit(5)\
                    .execute()

                if recent_missing.data:
                    print("\nRecent entities without embeddings:")
                    for entity in recent_missing.data:
                        name = entity.get("name", "N/A")
                        created = entity.get("created_at", "N/A")
                        print(f"  - {name} (created: {created})")

            return {
                "total": total,
                "with_embeddings": with_embeddings,
                "missing": missing,
                "coverage_percentage": coverage
            }

        except Exception as e:
            print(f"Error checking {entity_type}: {e}")
            return {
                "total": 0,
                "with_embeddings": 0,
                "missing": 0,
                "coverage_percentage": 0,
                "error": str(e)
            }

    def check_recent_creations(self, hours: int = 24) -> dict[str, Any]:
        """Check if recently created entities have embeddings."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()

        print(f"\n{'='*60}")
        print(f"RECENT CREATIONS (last {hours} hours)")
        print("="*60)

        total_recent = 0
        total_recent_missing = 0

        for entity_type, table_name in self.ENTITY_TYPES.items():
            try:
                # Recent entities
                recent = self.supabase.table(table_name)\
                    .select("id", count="exact")\
                    .gte("created_at", cutoff_str)\
                    .eq("is_deleted", False)\
                    .execute()

                recent_count = recent.count or 0

                # Recent without embeddings
                recent_missing = self.supabase.table(table_name)\
                    .select("id", count="exact")\
                    .gte("created_at", cutoff_str)\
                    .is_("embedding", "null")\
                    .eq("is_deleted", False)\
                    .execute()

                missing_count = recent_missing.count or 0

                total_recent += recent_count
                total_recent_missing += missing_count

                if recent_count > 0:
                    print(f"{entity_type}: {recent_count} created, {missing_count} missing embeddings")

            except Exception as e:
                print(f"Error checking recent {entity_type}: {e}")

        print(f"\nTotal: {total_recent} recent entities, {total_recent_missing} missing embeddings")

        return {
            "hours": hours,
            "total_recent": total_recent,
            "total_recent_missing": total_recent_missing
        }

    @staticmethod
    def _percentage(part: int, total: int) -> float:
        """Calculate percentage."""
        if total == 0:
            return 0.0
        return round((part / total) * 100, 2)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Check embedding status across all entities"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed information including recent entities without embeddings"
    )
    parser.add_argument(
        "--recent",
        type=int,
        default=24,
        help="Check entities created in the last N hours (default: 24)"
    )

    args = parser.parse_args()

    # Get credentials - use canonical variable names with fallbacks
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if url:
        url = url.strip().strip('"').strip("'").rstrip("/").rstrip("\n")
    if key:
        key = key.strip().strip('"').strip("'").rstrip("\n")

    if not url or not key:
        print("❌ Error: Missing Supabase credentials")
        print("   Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    # Create client
    supabase = create_client(url, key)

    # Check status
    checker = EmbeddingStatusChecker(supabase)
    status = checker.check_all_status(verbose=args.verbose)

    # Check recent creations
    if args.recent:
        checker.check_recent_creations(hours=args.recent)


if __name__ == "__main__":
    main()
