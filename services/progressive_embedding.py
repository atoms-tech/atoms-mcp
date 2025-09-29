"""Progressive embedding service that generates embeddings on-demand during search operations."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import asyncio

from supabase import Client
from .embedding_factory import get_embedding_service

logger = logging.getLogger(__name__)


class ProgressiveEmbeddingService:
    """Service that automatically generates embeddings on-demand during search operations."""
    
    def __init__(self, supabase_client: Client, embedding_service=None):
        self.supabase = supabase_client
        self.embedding_service = embedding_service or get_embedding_service()
        
        # Track records being processed to avoid duplicates
        self._processing_records: Set[str] = set()
        
        # Configuration for each table
        self.table_configs = {
            'documents': {
                'content_columns': ['content', 'description', 'name'],
                'embedding_column': 'embedding'
            },
            'requirements': {
                'content_columns': ['content', 'description', 'name'],
                'embedding_column': 'embedding'
            },
            'test_req': {
                'content_columns': ['content', 'description', 'name'],
                'embedding_column': 'embedding'
            },
            'projects': {
                'content_columns': ['description', 'name'],
                'embedding_column': 'embedding'
            },
            'organizations': {
                'content_columns': ['description', 'name'],
                'embedding_column': 'embedding'
            }
        }
    
    async def ensure_embeddings_for_search(
        self,
        entity_types: List[str],
        limit: Optional[int] = None,
        background: bool = True
    ) -> Dict[str, int]:
        """
        Ensure embeddings exist for records that will be searched.
        
        Args:
            entity_types: List of entity types to check
            limit: Optional limit on records to process per entity
            background: If True, generate embeddings in background (non-blocking)
        
        Returns:
            Dict with counts of embeddings generated per entity type
        """
        results = {}
        
        for entity_type in entity_types:
            table_name = self._get_table_name(entity_type)
            if not table_name or table_name not in self.table_configs:
                continue
            
            try:
                # Find records without embeddings
                missing_records = await self._find_records_without_embeddings(
                    table_name, limit or 50  # Reasonable batch size for search
                )
                
                if missing_records:
                    if background:
                        # Generate embeddings in background
                        asyncio.create_task(
                            self._generate_embeddings_for_records(table_name, missing_records)
                        )
                        results[entity_type] = f"Generating {len(missing_records)} embeddings in background"
                    else:
                        # Generate embeddings synchronously (blocks search)
                        generated = await self._generate_embeddings_for_records(table_name, missing_records)
                        results[entity_type] = f"Generated {generated} embeddings"
                else:
                    results[entity_type] = "All records have embeddings"
                    
            except Exception as e:
                logger.error(f"Error ensuring embeddings for {entity_type}: {e}")
                results[entity_type] = f"Error: {str(e)}"
        
        return results
    
    async def generate_embedding_on_demand(
        self,
        table_name: str,
        record_id: str,
        record_data: Optional[Dict[str, Any]] = None
    ) -> Optional[List[float]]:
        """
        Generate embedding for a single record on-demand.
        
        Args:
            table_name: Database table name
            record_id: Record ID
            record_data: Optional record data (to avoid extra DB query)
        
        Returns:
            Generated embedding vector or None if failed
        """
        record_key = f"{table_name}:{record_id}"
        
        # Prevent duplicate processing
        if record_key in self._processing_records:
            logger.debug(f"Record {record_key} already being processed")
            return None
        
        self._processing_records.add(record_key)
        
        try:
            # Get record data if not provided
            if record_data is None:
                record_data = await self._fetch_record(table_name, record_id)
                if not record_data:
                    return None
            
            # Extract content for embedding
            content = self._extract_content(record_data, table_name)
            if not content:
                logger.warning(f"No content found for {record_key}")
                return None
            
            # Generate embedding
            embedding_result = await self.embedding_service.generate_embedding(content)
            embedding_vector = embedding_result.embedding
            
            # Update record with embedding
            await self._update_record_embedding(table_name, record_id, embedding_vector)
            
            logger.info(f"Generated embedding for {record_key} ({len(content)} chars)")
            return embedding_vector
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for {record_key}: {e}")
            return None
        finally:
            self._processing_records.discard(record_key)
    
    async def _find_records_without_embeddings(
        self,
        table_name: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find records that don't have embeddings."""
        try:
            config = self.table_configs[table_name]
            
            # Select records without embeddings
            query = self.supabase.table(table_name).select('*')
            query = query.is_(config['embedding_column'], 'null')
            query = query.eq('is_deleted', False)
            query = query.limit(limit)
            query = query.order('updated_at', desc=True)  # Prioritize recent records
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error finding records without embeddings in {table_name}: {e}")
            return []
    
    async def _generate_embeddings_for_records(
        self,
        table_name: str,
        records: List[Dict[str, Any]]
    ) -> int:
        """Generate embeddings for a batch of records."""
        generated_count = 0
        
        for record in records:
            record_id = record.get('id')
            if not record_id:
                continue
            
            try:
                embedding = await self.generate_embedding_on_demand(
                    table_name, record_id, record
                )
                if embedding:
                    generated_count += 1
                    
                # Small delay to be nice to the API
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error generating embedding for {table_name}:{record_id}: {e}")
                continue
        
        logger.info(f"Generated {generated_count}/{len(records)} embeddings for {table_name}")
        return generated_count
    
    async def _fetch_record(self, table_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single record from the database."""
        try:
            result = self.supabase.table(table_name).select('*').eq('id', record_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error fetching record {table_name}:{record_id}: {e}")
            return None
    
    def _extract_content(self, record: Dict[str, Any], table_name: str) -> Optional[str]:
        """Extract content text from record for embedding."""
        config = self.table_configs.get(table_name, {})
        content_columns = config.get('content_columns', ['content', 'description', 'name'])
        
        for column in content_columns:
            content = record.get(column)
            if content and content.strip():
                return content.strip()
        
        return None
    
    async def _update_record_embedding(
        self,
        table_name: str,
        record_id: str,
        embedding: List[float]
    ) -> bool:
        """Update record with generated embedding."""
        try:
            config = self.table_configs[table_name]
            
            result = self.supabase.table(table_name).update({
                config['embedding_column']: embedding,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', record_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating embedding for {table_name}:{record_id}: {e}")
            return False
    
    def _get_table_name(self, entity_type: str) -> Optional[str]:
        """Map entity type to table name."""
        mapping = {
            'document': 'documents',
            'requirement': 'requirements', 
            'test': 'test_req',
            'project': 'projects',
            'organization': 'organizations'
        }
        return mapping.get(entity_type)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return {
            'currently_processing': len(self._processing_records),
            'processing_records': list(self._processing_records)
        }