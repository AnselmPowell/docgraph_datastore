# src/research_assistant/services/cache_manager.py
from django.db import transaction
from ..models import DocumentMetadata, DocumentSection, LLMResponseCache
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

class DocumentCacheManager:
    """Production-ready document cache using database"""
    
    async def get_document_data(
        self,
        document_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get document and sections from database"""
        try:
            # Get document metadata
            document = await DocumentMetadata.objects.filter(id=document_id).first()
            if not document:
                print(f"[CacheManager] Document {document_id} not found")
                return None

            # Get all sections
            sections = await DocumentSection.objects.filter(
                document_id=document_id
            ).order_by('page_number', 'position')

            if not sections:
                print(f"[CacheManager] No sections found for document {document_id}")
                return None

            print(f"[CacheManager] Retrieved document data from DB")
            print(f"[CacheManager] Found {len(sections)} sections")

            return {
                'document': document,
                'sections': sections
            }

        except Exception as e:
            print(f"[CacheManager] Database retrieval error: {str(e)}")
            return None

    async def store_llm_response(
        self,
        document_id: str,
        response_type: str,
        query_hash: str,
        response_data: Dict
    ) -> None:
        """Store LLM response in database"""
        try:
            await LLMResponseCache.objects.create(
                document_id=document_id,
                response_type=response_type,
                query_hash=query_hash,
                response_data=response_data
            )
            print(f"[CacheManager] Stored {response_type} response in DB")
            
        except Exception as e:
            print(f"[CacheManager] Failed to store LLM response: {str(e)}")

    async def get_llm_response(
        self,
        document_id: str,
        response_type: str,
        query_hash: str
    ) -> Optional[Dict]:
        """Get cached LLM response from database"""
        try:
            cached_response = await LLMResponseCache.objects.filter(
                document_id=document_id,
                response_type=response_type,
                query_hash=query_hash
            ).first()

            if cached_response:
                print(f"[CacheManager] Found cached {response_type} response")
                return cached_response.response_data

            print(f"[CacheManager] No cached {response_type} response found")
            return None

        except Exception as e:
            print(f"[CacheManager] Error retrieving LLM response: {str(e)}")
            return None

    @staticmethod
    def generate_query_hash(query_data: Dict) -> str:
        """Generate consistent hash for query parameters"""
        # Sort dict keys for consistent hashing
        sorted_data = json.dumps(query_data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()

    # Add to DocumentCacheManager

    def get_llm_response_sync(self, document_id: str, response_type: str, query_hash: str) -> Optional[Dict]:
        """Synchronous version of get_llm_response"""
        try:
            cached_response = LLMResponseCache.objects.filter(
                document_id=document_id,
                response_type=response_type,
                query_hash=query_hash
            ).first()

            if cached_response:
                print(f"[CacheManager] Found cached {response_type} response")
                return cached_response.response_data

            print(f"[CacheManager] No cached {response_type} response found")
            return None

        except Exception as e:
            print(f"[CacheManager] Error retrieving LLM response: {str(e)}")
            return None

    def store_llm_response_sync(self, document_id: str, response_type: str, query_hash: str, response_data: Dict) -> None:
        """Synchronous version of store_llm_response"""
        try:
            LLMResponseCache.objects.create(
                document_id=document_id,
                response_type=response_type,
                query_hash=query_hash,
                response_data=response_data
            )
            print(f"[CacheManager] Stored {response_type} response in DB")
            
        except Exception as e:
            print(f"[CacheManager] Failed to store LLM response: {str(e)}")

    def get_document_data_sync(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous method to get document data from DB"""
        print(f"[CacheManager] Checking cache for document: {document_id}")
        
        try:
            # Get document metadata
            document = DocumentMetadata.objects.select_related().filter(id=document_id).first()
            if not document:
                print(f"[CacheManager] No document found with ID: {document_id}")
                return None

            # Get sections
            sections = list(DocumentSection.objects.filter(
                document_id=document_id
            ).order_by('page_number', 'position'))

            if not sections:
                print(f"[CacheManager] No sections found for document")
                return None

            print(f"[CacheManager] Found cached document with {len(sections)} sections")
            
            # Transform sections to match your expected format
            processed_sections = []
            for section in sections:
                section_data = {
                    'content': {
                        'text': section.content,
                        'type': section.section_type,
                        'citations': section.citations or []
                    },
                    'section_id': section.section_id,
                    'page_number': section.page_number,
                    'position': section.position,
                    'pointer': {
                        'section_start': section.start_text,
                        'title_group_number': section.title_group_number,
                        'title_text': section.title_group_text
                    },
                    'metadata': {
                        'element_details': {
                            'table': section.table_data,
                            'visual': {'ocr_text': section.extracted_image_text} if section.extracted_image_text else None
                        },
                    }
                }
                processed_sections.append(section_data)

            return {
                'document': document,
                'sections': processed_sections
            }

        except Exception as e:
            print(f"[CacheManager] Error retrieving document data: {str(e)}")
            return None