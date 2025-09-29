#!/usr/bin/env python3
"""Progressive embedding backfill script for existing data.

This script generates embeddings for existing records in batches,
handles rate limiting, and can resume from where it left off.
"""

import os
import sys
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import argparse
import json

# Add the parent directory to the path so we can import from the project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import get_supabase
from services.embedding import EmbeddingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embedding_backfill.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmbeddingBackfiller:
    """Handles progressive embedding generation for existing data."""
    
    def __init__(self, batch_size: int = 10, dry_run: bool = False):
        self.supabase = get_supabase()
        self.embedding_service = EmbeddingService()
        self.batch_size = batch_size
        self.dry_run = dry_run
        
        # Table configurations
        self.tables = {
            'documents': {
                'content_column': 'content',
                'fallback_columns': ['description', 'name'],
                'embedding_column': 'embedding'
            },
            'requirements': {
                'content_column': 'content',
                'fallback_columns': ['description', 'name'],
                'embedding_column': 'embedding'
            },
            'test_req': {
                'content_column': 'content',
                'fallback_columns': ['description', 'name'],
                'embedding_column': 'embedding'
            },
            'projects': {
                'content_column': 'description',
                'fallback_columns': ['name'],
                'embedding_column': 'embedding'
            },
            'organizations': {
                'content_column': 'description',
                'fallback_columns': ['name'],
                'embedding_column': 'embedding'
            }
        }
    
    async def check_table_readiness(self, table_name: str) -> bool:
        """Check if table has the required embedding column."""
        try:
            # Try a simple query to check if embedding column exists
            result = self.supabase.table(table_name).select('id, embedding').limit(1).execute()
            logger.info(f"✅ Table {table_name} has embedding column")
            return True
        except Exception as e:
            logger.error(f"❌ Table {table_name} missing embedding column or not accessible: {e}")
            return False
    
    def get_content_text(self, record: Dict[str, Any], table_config: Dict[str, Any]) -> Optional[str]:
        """Extract content text from record using configured columns."""
        # Try primary content column first
        content = record.get(table_config['content_column'])
        if content and content.strip():
            return content.strip()
        
        # Try fallback columns
        for col in table_config.get('fallback_columns', []):
            fallback = record.get(col)
            if fallback and fallback.strip():
                return fallback.strip()
        
        logger.warning(f"No content found for record {record.get('id')} in table")
        return None
    
    async def get_records_needing_embeddings(self, table_name: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get records that don't have embeddings yet."""
        try:
            query = self.supabase.table(table_name).select('*')
            
            # Filter to records without embeddings and not deleted
            query = query.is_('embedding', 'null')
            query = query.eq('is_deleted', False)
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            records = result.data if result.data else []
            
            logger.info(f"Found {len(records)} records needing embeddings in {table_name}")
            return records
            
        except Exception as e:
            logger.error(f"Error fetching records from {table_name}: {e}")
            return []
    
    async def generate_embedding_for_record(self, record: Dict[str, Any], table_config: Dict[str, Any]) -> Optional[List[float]]:
        """Generate embedding for a single record."""
        content = self.get_content_text(record, table_config)
        if not content:
            return None
        
        try:
            # Generate embedding
            result = await self.embedding_service.generate_embedding(content)
            return result.embedding
        except Exception as e:
            logger.error(f"Error generating embedding for record {record.get('id')}: {e}")
            return None
    
    async def update_record_embedding(self, table_name: str, record_id: str, embedding: List[float]) -> bool:
        """Update a record with its embedding."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update {table_name}:{record_id} with embedding")
            return True
        
        try:
            result = self.supabase.table(table_name).update({
                'embedding': embedding,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', record_id).execute()
            
            if result.data:
                logger.debug(f"✅ Updated {table_name}:{record_id}")
                return True
            else:
                logger.error(f"❌ Failed to update {table_name}:{record_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating {table_name}:{record_id}: {e}")
            return False
    
    async def backfill_table(self, table_name: str) -> Dict[str, int]:
        """Backfill embeddings for a single table."""
        logger.info(f"🚀 Starting backfill for table: {table_name}")
        
        if not await self.check_table_readiness(table_name):
            return {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
        
        table_config = self.tables[table_name]
        stats = {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
        
        # Get all records needing embeddings
        records = await self.get_records_needing_embeddings(table_name)
        
        if not records:
            logger.info(f"✅ No records need embeddings in {table_name}")
            return stats
        
        logger.info(f"📊 Processing {len(records)} records in batches of {self.batch_size}")
        
        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            batch_start = i + 1
            batch_end = min(i + self.batch_size, len(records))
            
            logger.info(f"🔄 Processing batch {batch_start}-{batch_end} of {len(records)}")
            
            for record in batch:
                record_id = record.get('id')
                stats['processed'] += 1
                
                try:
                    # Generate embedding
                    embedding = await self.generate_embedding_for_record(record, table_config)
                    
                    if embedding is None:
                        logger.warning(f"⚠️  Skipping {table_name}:{record_id} - no content")
                        stats['skipped'] += 1
                        continue
                    
                    # Update record
                    success = await self.update_record_embedding(table_name, record_id, embedding)
                    
                    if success:
                        stats['successful'] += 1
                    else:
                        stats['failed'] += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {table_name}:{record_id}: {e}")
                    stats['failed'] += 1
            
            # Rate limiting - pause between batches
            if i + self.batch_size < len(records):
                logger.info("⏸️  Pausing 2 seconds between batches...")
                await asyncio.sleep(2)
        
        logger.info(f"✅ Completed {table_name}: {stats}")
        return stats
    
    async def backfill_all_tables(self, tables: Optional[List[str]] = None) -> Dict[str, Dict[str, int]]:
        """Backfill embeddings for all configured tables."""
        target_tables = tables or list(self.tables.keys())
        results = {}
        
        logger.info(f"🚀 Starting progressive embedding backfill")
        logger.info(f"📋 Target tables: {target_tables}")
        logger.info(f"⚙️  Batch size: {self.batch_size}")
        logger.info(f"🧪 Dry run: {self.dry_run}")
        
        start_time = datetime.now()
        
        for table_name in target_tables:
            if table_name not in self.tables:
                logger.error(f"❌ Unknown table: {table_name}")
                continue
            
            try:
                table_results = await self.backfill_table(table_name)
                results[table_name] = table_results
            except Exception as e:
                logger.error(f"❌ Failed to backfill {table_name}: {e}")
                results[table_name] = {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print summary
        logger.info(f"\n📊 BACKFILL SUMMARY")
        logger.info(f"⏱️  Duration: {duration}")
        logger.info(f"🎯 Tables processed: {len(results)}")
        
        total_stats = {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
        for table_name, stats in results.items():
            logger.info(f"   {table_name}: {stats}")
            for key in total_stats:
                total_stats[key] += stats[key]
        
        logger.info(f"🎉 TOTALS: {total_stats}")
        
        return results

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Progressive embedding backfill')
    parser.add_argument('--tables', nargs='+', help='Specific tables to backfill')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--check-only', action='store_true', help='Only check table readiness')
    
    args = parser.parse_args()
    
    backfiller = EmbeddingBackfiller(
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
    
    if args.check_only:
        logger.info("🔍 Checking table readiness...")
        for table_name in backfiller.tables.keys():
            await backfiller.check_table_readiness(table_name)
        return
    
    # Run the backfill
    try:
        results = await backfiller.backfill_all_tables(args.tables)
        
        # Save results to file
        with open(f'backfill_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info("✅ Backfill completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Backfill interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Backfill failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())