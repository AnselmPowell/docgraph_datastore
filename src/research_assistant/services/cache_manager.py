# # src/research_assistant/services/cache_manager.py
# from django.db import transaction
# from ..models import DocumentMetadata, DocumentSection, LLMResponseCache
# import hashlib
# from typing import Dict, Any, Optional, List
# from datetime import datetime
# import json

# class DocumentCacheManager:
#     """Production-ready document cache using database"""
    
#     async def get_document_data(
#         self,
#         document_id: str,
#     ) -> Optional[Dict[str, Any]]:
#         """Get document and sections from database"""
#         try:
#             # Get document metadata
#             document = await DocumentMetadata.objects.filter(id=document_id).first()
#             if not document:
#                 print(f"[CacheManager] Document {document_id} not found")
#                 return None

#             # Get all sections
#             sections = await DocumentSection.objects.filter(
#                 document_id=document_id
#             ).order_by('page_number', 'position')

#             if not sections:
#                 print(f"[CacheManager] No sections found for document {document_id}")
#                 return None

#             print(f"[CacheManager] Retrieved document data from DB")
#             print(f"[CacheManager] Found {len(sections)} sections")

#             return {
#                 'document': document,
#                 'sections': sections
#             }

#         except Exception as e:
#             print(f"[CacheManager] Database retrieval error: {str(e)}")
#             return None

#     async def store_llm_response(
#         self,
#         document_id: str,
#         response_type: str,
#         query_hash: str,
#         response_data: Dict
#     ) -> None:
#         """Store LLM response in database"""
#         try:
#             await LLMResponseCache.objects.create(
#                 document_id=document_id,
#                 response_type=response_type,
#                 query_hash=query_hash,
#                 response_data=response_data
#             )
#             print(f"[CacheManager] Stored {response_type} response in DB")
            
#         except Exception as e:
#             print(f"[CacheManager] Failed to store LLM response: {str(e)}")

#     async def get_llm_response(
#         self,
#         document_id: str,
#         response_type: str,
#         query_hash: str
#     ) -> Optional[Dict]:
#         """Get cached LLM response from database"""
#         try:
#             cached_response = await LLMResponseCache.objects.filter(
#                 document_id=document_id,
#                 response_type=response_type,
#                 query_hash=query_hash
#             ).first()

#             if cached_response:
#                 print(f"[CacheManager] Found cached {response_type} response")
#                 return cached_response.response_data

#             print(f"[CacheManager] No cached {response_type} response found")
#             return None

#         except Exception as e:
#             print(f"[CacheManager] Error retrieving LLM response: {str(e)}")
#             return None

#     @staticmethod
#     def generate_query_hash(query_data: Dict) -> str:
#         """Generate consistent hash for query parameters"""
#         # Sort dict keys for consistent hashing
#         sorted_data = json.dumps(query_data, sort_keys=True)
#         return hashlib.md5(sorted_data.encode()).hexdigest()

#     # Add to DocumentCacheManager

#     def get_llm_response_sync(self, document_id: str, response_type: str, query_hash: str) -> Optional[Dict]:
#         """Synchronous version of get_llm_response"""
#         try:
#             cached_response = LLMResponseCache.objects.filter(
#                 document_id=document_id,
#                 response_type=response_type,
#                 query_hash=query_hash
#             ).first()

#             if cached_response:
#                 print(f"[CacheManager] Found cached {response_type} response")
#                 return cached_response.response_data

#             print(f"[CacheManager] No cached {response_type} response found")
#             return None

#         except Exception as e:
#             print(f"[CacheManager] Error retrieving LLM response: {str(e)}")
#             return None

#     def store_llm_response_sync(self, document_id: str, response_type: str, query_hash: str, response_data: Dict) -> None:
#         """Synchronous version of store_llm_response"""
#         print(f"[CacheManager] Storing {response_type} response in DB")
#         try:
#             LLMResponseCache.objects.create(
#                 document_id=document_id,
#                 response_type=response_type,
#                 query_hash=query_hash,
#                 response_data=response_data
#             )
#             print(f"[CacheManager] Stored {response_type} response in DB")

            
#         except Exception as e:
#             print(f"[CacheManager] Failed to store LLM response: {str(e)}")

#     def get_document_data_sync(self, document_id: str) -> Optional[Dict[str, Any]]:
#         """Synchronous method to get document data from DB"""
#         print(f"[CacheManager] Checking cache for document: {document_id}")
        
#         try:
#             # Get document metadata
#             document = DocumentMetadata.objects.select_related().filter(id=document_id).first()
#             if not document:
#                 print(f"[CacheManager] No document found with ID: {document_id}")
#                 return None

#             # Get sections
#             sections = list(DocumentSection.objects.filter(
#                 document_id=document_id
#             ).order_by('section_start_page_number', 'position'))

#             if not sections:
#                 print(f"[CacheManager] No sections found for document")
#                 return None

#             print(f"[CacheManager] Found cached document with {len(sections)} sections")
            
#             # Transform sections to match your expected format
#             processed_sections = []
#             for section in sections:
#                 section_data = {
#                     'content': {
#                         'text': section.content,
#                         'type': section.section_type,
#                         'has_citations': section.has_citations,
#                     },
#                     'elements': section.elements,
#                     'citations': section.citations or [],
#                     'section_id': section.section_id,
#                     'section_start_page_number': section.section_start_page_number,
#                     'position': section.position,
#                     'pointer': {
#                         'section_start_text': section.start_text,
#                         'title_group_number': section.title_group_number,
#                         'title_text': section.title_group_text
#                     },
#                     'metadata': {
#                         'element_details': {
#                             'table': section.table_data,
#                             'visual': {'ocr_text': section.extracted_image_text} if section.extracted_image_text else None
#                         },
#                     }
#                 }
#                 processed_sections.append(section_data)

#             return {
#                 'document': document,
#                 'sections': processed_sections
#             }

#         except Exception as e:
#             print(f"[CacheManager] Error retrieving document data: {str(e)}")
#             return None




# src/research_assistant/services/cache_manager.py

from django.db import transaction
from django.db.models import Q
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ..models import (
    DocumentMetadata, 
    DocumentSection,
    LLMResponseCache
)

class DocumentCacheManager:
    """Production-ready document cache using database"""

    def check_existing_document(self, file_data: Dict) -> Optional[DocumentMetadata]:
        """Check if document exists based on name and content hash"""
        print(f"[CacheManager] Checking for existing document: {file_data['file_name']}")
        
        # # Generate document hash
        # doc_hash = self._generate_document_hash(
        #     file_data['file_name'],
        # )

        # print(f"[CacheManager] Generated document hash: {doc_hash}")
         
        # Check for existing document
        existing_doc = DocumentMetadata.objects.filter(
            Q(file_name=file_data['file_name']) 
            # & Q(metadata__document_hash=doc_hash)
        ).first()

        print(f"[CacheManager] does document exist")

        if existing_doc:
            print(f"[CacheManager] Found existing document: {existing_doc.id}")
            return existing_doc

        print(f"[CacheManager] No existing document found")
        return None


    def get_document_data_sync(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document data from DB"""
        print(f"[CacheManager] Getting document data: {document_id}")
        
        try:
            # Get document metadata
            document = DocumentMetadata.objects.select_related().filter(id=document_id).first()
            if not document:
                print(f"[CacheManager] No document found with ID: {document_id}")
                return None

            # Get sections
            sections = list(DocumentSection.objects.filter(
                document_id=document_id
            ).order_by('section_start_page_number', 'position'))

            if not sections:
                print(f"[CacheManager] No sections found for document")
                return None

            print(f"[CacheManager] Found document with {len(sections)} sections")
            
            # Format sections
            processed_sections = []
            for section in sections:
                section_data = {
                    'content': {
                        'text': section.content,
                        'type': section.section_type,
                        'has_citations': section.has_citations,
                    },
                    'elements': section.elements,
                    'citations': section.citations or [],
                    'section_id': section.section_id,
                    'section_start_page_number': section.section_start_page_number,
                    'position': section.position,
                    'pointer': {
                        'section_start_text': section.start_text,
                        'title_group_number': section.title_group_number,
                        'title_text': section.title_group_text
                    }
                }
                processed_sections.append(section_data)

            # Return formatted data
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
                'sections': processed_sections
            }

        except Exception as e:
            print(f"[CacheManager] Error retrieving document data: {str(e)}")
            return None

    def get_search_cache_sync(
        self,
        document_ids: List[str],
        context: str,
        theme: str,
        keywords: List[str]
    ) -> Optional[Dict]:
        """Get cached search results"""
        try:
            query_hash = self._generate_search_hash(document_ids, context, theme, keywords)
            
            # Check cache for any document
            cached = LLMResponseCache.objects.filter(
                document_id__in=document_ids,
                response_type='search',
                query_hash=query_hash
            ).first()

            if cached:
                print(f"[CacheManager] Found cached search results")
                return cached.response_data

            return None

        except Exception as e:
            print(f"[CacheManager] Error retrieving search cache: {str(e)}")
            return None

    def store_search_cache_sync(
        self,
        document_ids: List[str],
        context: str,
        theme: str,
        keywords: List[str],
        results: Dict
    ) -> None:
        """Store search results in cache"""
        try:
            
            # Store for each document
            for doc_id in document_ids:
                query_hash = self._generate_search_hash(doc_id, context, theme, keywords)
                LLMResponseCache.objects.update_or_create(
                    document_id=doc_id,
                    response_type='search',
                    query_hash=query_hash,
                    defaults={'response_data': results}
                )
                
            print(f"[CacheManager] Stored search results in cache")

        except Exception as e:
            print(f"[CacheManager] Error storing search cache: {str(e)}")

    def _generate_document_hash(self, file_name: str) -> str:
        """Generate consistent document hash"""
        print(f"[CacheManager] Generating document hash")
        hash_input = f"{file_name}"
        return hash_input

    def _generate_search_hash(
        self,
        document_ids: List[str],
        context: str,
        theme: str,
        keywords: List[str]
    ) -> str:
        """Generate consistent search query hash"""
        # Sort inputs for consistency
        sorted_ids = sorted(document_ids)
        sorted_keywords = sorted(keywords)
        
        # Create hash input
        hash_input = f"{','.join(sorted_ids)}:{context}:{theme}:{','.join(sorted_keywords)}"
        return hashlib.md5(hash_input.encode()).hexdigest()