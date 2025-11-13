"""
API endpoint for processing embedding queue.
This is called by Vercel Cron to automatically generate embeddings.

Endpoint: /api/embeddings/process-queue
Method: POST (with cron secret for security)
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from supabase import create_client
from services.embedding_vertex import VertexAIEmbeddingService

logger = logging.getLogger(__name__)


async def process_embedding_queue_endpoint(
    batch_size: int = 20,
    cron_secret: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process embedding queue - generate embeddings for pending items.

    Args:
        batch_size: Number of items to process
        cron_secret: Secret key for cron authentication

    Returns:
        Dict with processing results
    """
    start_time = datetime.now()

    # Verify cron secret (security)
    expected_secret = os.getenv("CRON_SECRET")
    if expected_secret and cron_secret != expected_secret:
        return {
            "error": "Unauthorized",
            "message": "Invalid cron secret"
        }

    try:
        # Initialize services
        supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not supabase_url or not supabase_key:
            return {
                "error": "Configuration Error",
                "message": "Missing Supabase credentials"
            }

        # Strip quotes
        supabase_url = supabase_url.strip().strip('"').strip("'").rstrip('/')
        supabase_key = supabase_key.strip().strip('"').strip("'")

        supabase = create_client(supabase_url, supabase_key)
        embedding_service = VertexAIEmbeddingService()

        # Get pending items
        response = supabase.table('embedding_queue')\
            .select('*')\
            .eq('status', 'pending')\
            .order('created_at')\
            .limit(batch_size)\
            .execute()

        items = response.data or []

        if not items:
            return {
                "success": True,
                "message": "Queue is empty",
                "processed": 0,
                "succeeded": 0,
                "failed": 0
            }

        # Process items
        processed = 0
        succeeded = 0
        failed = 0
        errors = []

        for item in items:
            item_id = item['id']
            table_name = item['table_name']
            row_id = item['row_id']
            text_content = item['text_content']

            try:
                # Mark as processing
                supabase.table('embedding_queue')\
                    .update({'status': 'processing'})\
                    .eq('id', item_id)\
                    .execute()

                # Generate embedding
                result = await embedding_service.generate_embedding(text_content)

                # Update target table
                supabase.table(table_name)\
                    .update({'embedding': result.embedding})\
                    .eq('id', row_id)\
                    .execute()

                # Mark as completed
                supabase.table('embedding_queue')\
                    .update({
                        'status': 'completed',
                        'processed_at': datetime.now().isoformat()
                    })\
                    .eq('id', item_id)\
                    .execute()

                succeeded += 1
                logger.info(f"✅ Processed {table_name}:{row_id}")

            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Failed to process {table_name}:{row_id}: {error_msg}")

                # Update retry count
                new_retry = item.get('retry_count', 0) + 1
                new_status = 'failed' if new_retry >= 3 else 'pending'

                supabase.table('embedding_queue')\
                    .update({
                        'status': new_status,
                        'error_message': error_msg[:500],
                        'retry_count': new_retry
                    })\
                    .eq('id', item_id)\
                    .execute()

                failed += 1
                errors.append({
                    'table': table_name,
                    'row_id': row_id,
                    'error': error_msg[:200]
                })

            processed += 1

            # Rate limiting
            await asyncio.sleep(0.1)

        duration = (datetime.now() - start_time).total_seconds()

        return {
            "success": True,
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "duration_seconds": duration,
            "errors": errors if errors else None
        }

    except Exception as e:
        logger.error(f"❌ Queue processing failed: {e}")
        return {
            "error": "Internal Error",
            "message": str(e)
        }
