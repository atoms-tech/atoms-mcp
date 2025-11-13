#!/usr/bin/env python3
"""
Process embedding queue - continuously generate embeddings for queued items.

This service processes the embedding_queue table and generates embeddings
for items added by database triggers.

Usage:
    # Process queue once
    python scripts/process_embedding_queue.py

    # Continuous processing (daemon mode)
    python scripts/process_embedding_queue.py --daemon

    # Process with custom batch size
    python scripts/process_embedding_queue.py --batch-size 50

    # Run as background service
    nohup python scripts/process_embedding_queue.py --daemon > embedding_queue.log 2>&1 &
"""

import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.embedding_vertex import VertexAIEmbeddingService
from supabase import create_client, Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingQueueProcessor:
    """Service for processing the embedding queue."""

    def __init__(self, batch_size: int = 10, max_retries: int = 3):
        """Initialize the queue processor.

        Args:
            batch_size: Number of queue items to process at once
            max_retries: Maximum retry attempts for failed items
        """
        self.batch_size = batch_size
        self.max_retries = max_retries

        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not supabase_url or not supabase_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set"
            )

        # Strip quotes
        supabase_url = supabase_url.strip().strip('"').strip("'").rstrip('/')
        supabase_key = supabase_key.strip().strip('"').strip("'")

        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Initialize Vertex AI embedding service
        self.embedding_service = VertexAIEmbeddingService()

        # Track statistics
        self.stats = {
            'total_processed': 0,
            'total_succeeded': 0,
            'total_failed': 0,
            'start_time': datetime.now()
        }

    async def get_pending_items(self) -> List[Dict]:
        """Fetch pending items from queue."""
        response = self.supabase.table('embedding_queue')\
            .select('*')\
            .eq('status', 'pending')\
            .order('created_at')\
            .limit(self.batch_size)\
            .execute()

        return response.data or []

    async def process_queue_item(self, item: Dict) -> bool:
        """Process a single queue item.

        Args:
            item: Queue item dictionary

        Returns:
            True if successful, False otherwise
        """
        item_id = item['id']
        table_name = item['table_name']
        row_id = item['row_id']
        text_content = item['text_content']
        retry_count = item['retry_count']

        try:
            # Mark as processing
            self.supabase.table('embedding_queue')\
                .update({'status': 'processing'})\
                .eq('id', item_id)\
                .execute()

            # Generate embedding
            result = await self.embedding_service.generate_embedding(text_content)

            # Update target table with embedding
            self.supabase.table(table_name)\
                .update({'embedding': result.embedding})\
                .eq('id', row_id)\
                .execute()

            # Mark as completed
            self.supabase.table('embedding_queue')\
                .update({
                    'status': 'completed',
                    'processed_at': datetime.now().isoformat()
                })\
                .eq('id', item_id)\
                .execute()

            self.stats['total_succeeded'] += 1
            cached_emoji = "✅" if result.cached else "🔄"
            logger.info(f"✅ {cached_emoji} {table_name}:{row_id}")

            return True

        except Exception as e:
            error_msg = str(e)
            logger.error(f"L Error processing {table_name}:{row_id}: {error_msg}")

            # Update status based on retry count
            new_retry_count = retry_count + 1
            new_status = 'failed' if new_retry_count >= self.max_retries else 'pending'

            self.supabase.table('embedding_queue')\
                .update({
                    'status': new_status,
                    'error_message': error_msg[:500],  # Truncate long errors
                    'retry_count': new_retry_count,
                    'processed_at': datetime.now().isoformat() if new_status == 'failed' else None
                })\
                .eq('id', item_id)\
                .execute()

            self.stats['total_failed'] += 1
            return False

        finally:
            self.stats['total_processed'] += 1

    async def process_batch(self) -> int:
        """Process one batch of pending items.

        Returns:
            Number of items processed
        """
        items = await self.get_pending_items()

        if not items:
            return 0

        logger.info(f"=� Processing batch of {len(items)} items...")

        # Process items sequentially with rate limiting
        for item in items:
            await self.process_queue_item(item)
            await asyncio.sleep(0.1)  # 100ms rate limiting

        return len(items)

    async def run_once(self):
        """Process queue once and exit."""
        logger.info("=� Processing embedding queue (one-time)...")

        total_processed = 0

        while True:
            count = await self.process_batch()
            if count == 0:
                break
            total_processed += count

        self._print_summary()
        logger.info(f" Processed {total_processed} items")

    async def run_daemon(self, poll_interval: int = 60):
        """Run continuously as a daemon.

        Args:
            poll_interval: Seconds to wait between queue checks
        """
        logger.info("= Starting embedding queue processor (daemon mode)...")
        logger.info(f"   Polling interval: {poll_interval}s")
        logger.info(f"   Batch size: {self.batch_size}")
        logger.info(f"   Max retries: {self.max_retries}")

        try:
            while True:
                try:
                    count = await self.process_batch()

                    if count > 0:
                        logger.info(f" Processed batch of {count} items")
                        # If we processed a full batch, check immediately for more
                        if count >= self.batch_size:
                            continue
                    else:
                        logger.debug("�  Queue empty, waiting...")

                    # Print stats periodically
                    if self.stats['total_processed'] > 0 and self.stats['total_processed'] % 100 == 0:
                        self._print_summary()

                    # Wait before next poll
                    await asyncio.sleep(poll_interval)

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"L Error in daemon loop: {str(e)}")
                    await asyncio.sleep(poll_interval)

        except KeyboardInterrupt:
            logger.info("\n�  Daemon stopped by user")
            self._print_summary()

    def _print_summary(self):
        """Print current statistics."""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        rate = self.stats['total_processed'] / max(duration, 1)

        print("\n" + "="*60)
        print("=� QUEUE PROCESSOR STATS")
        print("="*60)
        print(f"Runtime: {duration:.2f}s")
        print(f"Total processed: {self.stats['total_processed']}")
        print(f" Succeeded: {self.stats['total_succeeded']}")
        print(f"L Failed: {self.stats['total_failed']}")
        print(f"Rate: {rate:.2f} items/sec")
        print("="*60 + "\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Process embedding queue',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run continuously as a daemon'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Batch size for processing (default: 10)'
    )

    parser.add_argument(
        '--poll-interval',
        type=int,
        default=60,
        help='Seconds between queue checks in daemon mode (default: 60)'
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts for failed items (default: 3)'
    )

    args = parser.parse_args()

    # Load environment
    from dotenv import load_dotenv
    load_dotenv('.env', override=True)
    load_dotenv('.env.production', override=False)

    # Create processor
    processor = EmbeddingQueueProcessor(
        batch_size=args.batch_size,
        max_retries=args.max_retries
    )

    # Run
    if args.daemon:
        await processor.run_daemon(poll_interval=args.poll_interval)
    else:
        await processor.run_once()


if __name__ == '__main__':
    asyncio.run(main())
