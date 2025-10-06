#!/usr/bin/env python3
"""Backfill embeddings for existing entities.

This script generates embeddings for all entities that don't have them yet.
Uses the progressive embedding service for efficient batch processing.

Usage:
    python scripts/backfill_embeddings.py [--entity-type TYPE] [--limit N] [--dry-run]

Examples:
    # Backfill all entities
    python scripts/backfill_embeddings.py

    # Backfill only organizations
    python scripts/backfill_embeddings.py --entity-type organization

    # Dry run to see what would be processed
    python scripts/backfill_embeddings.py --dry-run

    # Process only first 10 entities
    python scripts/backfill_embeddings.py --limit 10
"""

import asyncio
import os
import sys
import argparse
import warnings
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from tqdm.asyncio import tqdm
from concurrent.futures import ThreadPoolExecutor

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*ALTS.*')
warnings.filterwarnings('ignore', message='.*deprecated.*')

# Suppress gRPC/ALTS logging
logging.getLogger('grpc').setLevel(logging.ERROR)
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = ''

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
# Load .env first (has correct Supabase URL), then .env.production for other vars
load_dotenv('.env', override=True)  # Load .env first
load_dotenv('.env.production', override=False)  # Add production vars that aren't already set


class EmbeddingBackfiller:
    """Service to backfill embeddings for existing entities."""

    # Entity types that support embeddings
    ENTITY_TYPES = [
        "organization",
        "project",
        "document",
        "requirement"
    ]

    # Map entity type to table name
    TABLE_MAP = {
        "organization": "organizations",
        "project": "projects",
        "document": "documents",
        "requirement": "requirements"
    }

    def __init__(self, supabase: Client, dry_run: bool = False, concurrency: int = 5):
        self.supabase = supabase
        self.dry_run = dry_run
        self.concurrency = concurrency
        self._embedding_service = None
        self._progressive_service = None
        self._semaphore = None
        self._pbar_lock = None
        # Timing statistics
        self._timing_stats = {
            'embedding': [],
            'db_update': [],
            'total': []
        }

    def _init_services(self):
        """Lazy init embedding services."""
        if self._embedding_service is None:
            from services.embedding_factory import get_embedding_service
            from services.progressive_embedding import ProgressiveEmbeddingService

            self._embedding_service = get_embedding_service()
            self._progressive_service = ProgressiveEmbeddingService(
                self.supabase,
                self._embedding_service
            )
            self._semaphore = asyncio.Semaphore(self.concurrency)
            self._pbar_lock = asyncio.Lock()

    async def count_missing_embeddings(
        self,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """Count entities without embeddings by type."""
        entity_types = entity_types or self.ENTITY_TYPES
        counts = {}

        for entity_type in entity_types:
            table = self.TABLE_MAP[entity_type]

            try:
                result = self.supabase.table(table)\
                    .select("id", count="exact")\
                    .is_("embedding", None)\
                    .eq("is_deleted", False)\
                    .execute()

                counts[entity_type] = result.count or 0
            except Exception as e:
                print(f"⚠️  Error counting {entity_type}: {e}")
                counts[entity_type] = 0

        return counts

    async def get_entities_without_embeddings(
        self,
        entity_type: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get entities that don't have embeddings."""
        table = self.TABLE_MAP[entity_type]

        if limit:
            # If user specified limit, just fetch that many
            query = self.supabase.table(table)\
                .select("*")\
                .is_("embedding", None)\
                .eq("is_deleted", False)\
                .order("created_at", desc=True)\
                .limit(limit)
            result = query.execute()
            return result.data or []

        # No limit specified - fetch ALL records using pagination
        # Supabase has max 1000 per page
        all_entities = []
        page_size = 1000
        offset = 0

        while True:
            query = self.supabase.table(table)\
                .select("*")\
                .is_("embedding", None)\
                .eq("is_deleted", False)\
                .order("created_at", desc=True)\
                .range(offset, offset + page_size - 1)

            result = query.execute()
            if not result.data:
                break

            all_entities.extend(result.data)

            # If we got less than page_size, we're done
            if len(result.data) < page_size:
                break

            offset += page_size

        return all_entities

    async def _process_single_entity(
        self,
        table: str,
        entity: Dict[str, Any],
        stats: Dict[str, Any],
        pbar: tqdm = None
    ):
        """Process a single entity with semaphore concurrency control."""
        import time
        start_time = time.time()

        async with self._semaphore:
            entity_id = entity["id"]
            name = entity.get('name') or entity.get('title') or entity_id[:8]

            try:
                result = await self._progressive_service.generate_embedding_on_demand(
                    table,
                    entity_id,
                    entity
                )

                elapsed = time.time() - start_time

                # Verify the embedding was actually created
                if result is not None:
                    stats["succeeded"] += 1

                    # Collect timing stats
                    timings = result.get('timings', {})
                    self._timing_stats['embedding'].append(timings.get('embedding', 0))
                    self._timing_stats['db_update'].append(timings.get('db_update', 0))
                    self._timing_stats['total'].append(elapsed)

                    # Calculate averages
                    avg_embed = sum(self._timing_stats['embedding']) / len(self._timing_stats['embedding'])
                    avg_db = sum(self._timing_stats['db_update']) / len(self._timing_stats['db_update'])

                    status = f"✅ {name[:20]} | emb:{timings.get('embedding', 0):.2f}s db:{timings.get('db_update', 0):.2f}s | avg: {avg_embed:.2f}s/{avg_db:.2f}s"
                else:
                    stats["failed"] += 1
                    stats["errors"].append({
                        "entity_id": entity_id,
                        "name": name,
                        "error": "generate_embedding_on_demand returned None"
                    })
                    status = f"⚠️  {name[:25]} ({elapsed:.2f}s)"

            except Exception as e:
                elapsed = time.time() - start_time
                error_msg = str(e)
                stats["failed"] += 1
                stats["errors"].append({
                    "entity_id": entity_id,
                    "name": name,
                    "error": error_msg
                })
                status = f"❌ {name[:25]} ({elapsed:.2f}s)"

            finally:
                stats["processed"] += 1
                # Update progress bar
                if pbar:
                    pbar.update(1)
                    # Update postfix every item to show timing
                    pbar.set_postfix_str(status)

    async def backfill_entity_type(
        self,
        entity_type: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Backfill embeddings for a specific entity type with concurrency."""
        self._init_services()

        table = self.TABLE_MAP[entity_type]

        print(f"\n{'='*60}")
        print(f"Processing: {entity_type.upper()} (concurrency: {self.concurrency})")
        print(f"{'='*60}")

        # Get entities without embeddings
        entities = await self.get_entities_without_embeddings(entity_type, limit)

        if not entities:
            print(f"✅ No {entity_type}s need embeddings - all up to date!")
            return {
                "entity_type": entity_type,
                "total": 0,
                "processed": 0,
                "succeeded": 0,
                "failed": 0,
                "skipped": 0
            }

        if self.dry_run:
            print(f"🔍 DRY RUN - Would process {len(entities)} entities:")
            for i, entity in enumerate(entities[:5], 1):  # Show first 5
                name = entity.get('name') or entity.get('title') or entity.get('id')
                print(f"  {i}. {name}")
            if len(entities) > 5:
                print(f"  ... and {len(entities) - 5} more")
            return {
                "entity_type": entity_type,
                "total": len(entities),
                "processed": 0,
                "succeeded": 0,
                "failed": 0,
                "skipped": len(entities)
            }

        # Process entities concurrently
        stats = {
            "entity_type": entity_type,
            "total": len(entities),
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "errors": []
        }

        # Create progress bar with file object to control output
        import sys
        pbar = tqdm(
            total=len(entities),
            desc=f"{entity_type.capitalize():<15}",
            unit="item",
            ncols=120,
            leave=True,
            file=sys.stdout,
            ascii=False,
            dynamic_ncols=False
        )

        try:
            # Create ALL tasks at once - let semaphore handle concurrency
            tasks = [
                self._process_single_entity(table, entity, stats, pbar)
                for entity in entities
            ]

            # Run all tasks concurrently with semaphore limiting concurrency
            await asyncio.gather(*tasks)
        finally:
            pbar.close()

        # Summary
        print(f"\n📈 Summary for {entity_type}:")
        print(f"  Total: {stats['total']}")
        print(f"  ✅ Succeeded: {stats['succeeded']}")
        print(f"  ❌ Failed: {stats['failed']}")

        # Show error details if any failures occurred
        if stats['failed'] > 0 and stats.get('errors'):
            print(f"\n⚠️  Error Details:")
            for i, error in enumerate(stats['errors'][:5], 1):  # Show first 5 errors
                print(f"  {i}. {error['name'][:40]}: {error['error'][:60]}")
            if len(stats['errors']) > 5:
                print(f"  ... and {len(stats['errors']) - 5} more errors")

        return stats

    async def backfill_all(
        self,
        entity_types: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Backfill embeddings for all entity types."""
        entity_types = entity_types or self.ENTITY_TYPES

        print("\n" + "="*60)
        print("🚀 EMBEDDING BACKFILL PROCESS")
        print("="*60)

        # First, show counts
        print("\n📊 Counting entities without embeddings...")
        counts = await self.count_missing_embeddings(entity_types)

        total_missing = sum(counts.values())

        print("\n📋 Current Status:")
        for entity_type, count in counts.items():
            print(f"  - {entity_type}: {count} missing embeddings")
        print(f"\n  TOTAL: {total_missing} entities need embeddings")

        if total_missing == 0:
            print("\n✅ All entities already have embeddings!")
            return {"total_missing": 0, "results": []}

        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No embeddings will be generated")

        # Process each entity type
        results = []
        overall_stats = {
            "total": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0
        }

        for entity_type in entity_types:
            if counts[entity_type] > 0:
                stats = await self.backfill_entity_type(entity_type, limit)
                results.append(stats)

                overall_stats["total"] += stats["total"]
                overall_stats["succeeded"] += stats["succeeded"]
                overall_stats["failed"] += stats["failed"]
                overall_stats["skipped"] += stats.get("skipped", 0)

        # Final summary
        print("\n" + "="*60)
        print("🎉 BACKFILL COMPLETE")
        print("="*60)
        print(f"  Total entities: {overall_stats['total']}")
        print(f"  ✅ Succeeded: {overall_stats['succeeded']}")
        print(f"  ❌ Failed: {overall_stats['failed']}")
        if overall_stats["skipped"] > 0:
            print(f"  ⏭️  Skipped (dry run): {overall_stats['skipped']}")

        return {
            "total_missing": total_missing,
            "overall_stats": overall_stats,
            "results": results
        }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill embeddings for existing entities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--entity-type",
        choices=EmbeddingBackfiller.ENTITY_TYPES + ["all"],
        default="all",
        help="Entity type to backfill (default: all)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of entities to process per type"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually generating embeddings"
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent embedding generation tasks (default: 5)"
    )

    args = parser.parse_args()

    # Check environment
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # Strip quotes and whitespace (common in .env files)
    if url:
        url = url.strip().strip('"').strip("'").rstrip('/').rstrip('\n')
    if key:
        key = key.strip().strip('"').strip("'").rstrip('\n')

    if not url or not key:
        print("❌ Error: Missing Supabase credentials")
        print("   Required environment variables:")
        print("   - NEXT_PUBLIC_SUPABASE_URL")
        print("   - SUPABASE_SERVICE_ROLE_KEY")
        print("\n   Make sure .env or .env.production is properly configured")
        print(f"\n   Debug: URL={url[:30] if url else 'None'}...")
        print(f"   Debug: KEY={'***' + key[-10:] if key else 'None'}")
        sys.exit(1)

    print(f"🔗 Connecting to Supabase: {url}")
    print(f"🔑 Using service role key: ***{key[-10:]}")

    # Check embedding service
    try:
        from services.embedding_factory import get_embedding_service
        service = get_embedding_service()
        print(f"✅ Embedding service initialized: {service.__class__.__name__}")
    except Exception as e:
        print(f"❌ Error initializing embedding service: {e}")
        print("   Make sure Vertex AI or OpenAI credentials are configured")
        sys.exit(1)

    # Create Supabase client
    supabase = create_client(url, key)

    # Create backfiller
    backfiller = EmbeddingBackfiller(
        supabase,
        dry_run=args.dry_run,
        concurrency=args.concurrency
    )

    # Determine entity types to process
    if args.entity_type == "all":
        entity_types = None  # Process all
    else:
        entity_types = [args.entity_type]

    # Run backfill
    try:
        results = await backfiller.backfill_all(
            entity_types=entity_types,
            limit=args.limit
        )

        # Exit with error code if any failed
        if results.get("overall_stats", {}).get("failed", 0) > 0:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Backfill interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Redirect stderr to /dev/null to suppress C++ gRPC ALTS warnings
    # These warnings come from the C++ layer and can't be suppressed by Python's warning module
    import fcntl

    # Save original stderr
    original_stderr_fd = sys.stderr.fileno()
    original_stderr = os.dup(original_stderr_fd)

    # Create a pipe for filtered stderr
    read_fd, write_fd = os.pipe()

    # Redirect stderr to write end of pipe
    os.dup2(write_fd, original_stderr_fd)
    os.close(write_fd)

    # Make the read end non-blocking
    flags = fcntl.fcntl(read_fd, fcntl.F_GETFL)
    fcntl.fcntl(read_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    # Start a thread to filter stderr
    import threading
    import select

    def filter_stderr():
        """Filter stderr output to suppress ALTS warnings."""
        while True:
            try:
                # Check if there's data to read
                ready, _, _ = select.select([read_fd], [], [], 0.1)
                if ready:
                    data = os.read(read_fd, 8192)
                    if not data:
                        break

                    # Decode and filter
                    text = data.decode('utf-8', errors='replace')
                    lines = text.split('\n')

                    for line in lines:
                        # Skip ALTS and deprecation warnings
                        if 'ALTS creds ignored' in line or 'deprecated as of' in line or 'UserWarning' in line:
                            continue
                        if line.strip():
                            os.write(original_stderr, (line + '\n').encode('utf-8'))
            except (OSError, ValueError):
                break

    filter_thread = threading.Thread(target=filter_stderr, daemon=True)
    filter_thread.start()

    try:
        asyncio.run(main())
    finally:
        # Restore original stderr
        os.dup2(original_stderr, original_stderr_fd)
        os.close(original_stderr)
        os.close(read_fd)
