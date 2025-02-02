# src/research_assistant/services/cache_manager.py

# cache_manager.py
from django.db import transaction
from django.db.models import Q
import hashlib
from typing import Dict, List, Any, Optional

from ..models import DocumentMetadata, DocumentSection, LLMResponseCache

class DocumentCacheManager:
    """Production-ready document cache using database"""

    def check_existing_document(self, file_data: Dict) -> Optional[DocumentMetadata]:
        """Check if document exists based on filename"""
        print(f"[CacheManager] Checking for existing document: {file_data['file_name']}")
        
        existing_doc = DocumentMetadata.objects.filter(
            file_name=file_data['file_name']
        ).first()

        if existing_doc:
            print(f"[CacheManager] Found existing document: {existing_doc.id}")
            return existing_doc

        print(f"[CacheManager] No existing document found")
        return None


    def get_document_data_sync(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document data from DB"""
        try:
            # Get document
            document = DocumentMetadata.objects.select_related().filter(id=document_id).first()
            if not document:
                return None

            # Get sections
            sections = list(DocumentSection.objects.filter(
                document_id=document_id
            ).order_by('section_start_page_number'))

            if not sections:
                return None

            # Format sections
            processed_sections = []
            for section in sections:
                section_data = {
                    'content': {
                        'text': section.content,
                        'type': section.section_type,
                        'has_citations': section.has_citations
                    },
                    'prev_page_text': section.prev_page_text,
                    'next_page_text': section.next_page_text,
                    'citations': section.citations or [],
                    'elements': section.get_elements(),
                    'section_start_page_number': section.section_start_page_number
                }
                processed_sections.append(section_data)

            return {
                'document': {
                    'document_id': str(document.id),
                    'title': document.title,
                    'authors': document.authors,
                    'summary': document.summary,
                    'references': document.reference,
                    'processing_status': document.processing_status,
                    'file_name': document.file_name,
                    'file_url': document.url,
                    'created_at': document.created_at
                },
                'sections': processed_sections,
                'reference_data': document.reference  # Added this line
            }

        except Exception as e:
            print(f"[CacheManager] Error retrieving document data: {str(e)}")
            return None


    def get_search_cache_sync(
        self,
        documents,
        context: str,
        keywords: List[str]
    ) -> Optional[Dict]:
        
        print("[Cache seach]: document file name", documents)
        query_hash = self._generate_search_hash(documents["file_name"], context, keywords)
        
        cached = LLMResponseCache.objects.filter(
            file_name=documents["file_name"],
            response_type='search',
            query_hash=query_hash
        ).first()

        if cached:
            print(f"[CacheManager] Found cached search results")
            return cached.response_data

        return None

       

    def store_search_cache_sync(
        self,
        documents,
        context: str,
        keywords: List[str],
        results: Dict
    ) -> None:
        try:
            for doc in documents:
                query_hash = self._generate_search_hash(doc, context, keywords)
                LLMResponseCache.objects.update_or_create(
                    file_name=doc["file_name"],
                    response_type='search',
                    query_hash=query_hash,
                    defaults={'response_data': results}
                )
                
            print(f"[CacheManager] Stored search results in cache")

        except Exception as e:
            print(f"[CacheManager] Error storing search cache: {str(e)}")

    def _generate_search_hash(
        self,
        document_ids: List[str],
        context: str,
        keywords: List[str]
    ) -> str:
        sorted_ids = sorted(document_ids)
        sorted_keywords = sorted(keywords)
        hash_input = f"{','.join(sorted_ids)}:{context}:{','.join(sorted_keywords)}"
        return hashlib.md5(hash_input.encode()).hexdigest()