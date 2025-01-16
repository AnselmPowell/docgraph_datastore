# # src/research_assistant/views.py
# from rest_framework import viewsets, status
# from rest_framework.decorators import action 
# from rest_framework.response import Response
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator
# from asgiref.sync import sync_to_async, async_to_sync
# import asyncio
# from typing import Dict, List
# import json
 
# from .models import DocumentMetadata, DocumentSection
# from .services.document_processor import DocumentProcessor
# from .services.document_summarizer import DocumentSummarizer
# from .services.document_searcher import DocumentSearcher

# from django.db import connection
# from .services.cache_manager import DocumentCacheManager



# @method_decorator(csrf_exempt, name='dispatch')
# class ResearchAnalysisViewSet(viewsets.ViewSet):
#     """Handle document analysis and search requests"""
    
#     def __init__(self, **kwargs):
#         # super().__init__(**kwargs)
#         self.cache_manager = DocumentCacheManager()
#         print("[ResearchAnalysisViewSet] Initialized with API Call")

#     async def _process_single_document(
#         self,
#         file_data: Dict,
#         context: str,
#         theme: str,
#         keywords: List[str],
#         processor: DocumentProcessor,
#         summarizer: DocumentSummarizer,
#         searcher: DocumentSearcher
#     ) -> Dict:
#         """Process a single document and return results"""  
#         print("[_process_single_document] Inside process single document ")  
#         print(f"[_process_single_document] Processing document: {file_data['file_name']}")
#         print(f"[_process_single_document] URL: {file_data['file_url']}")

    
#         doc_id = None
#         existing_document = await sync_to_async(lambda: DocumentMetadata.objects.filter(
#             file_name=file_data['file_name']
#         ).first())()

#         if existing_document:
#             print(f"Document already exists with ID: {existing_document.id}")
#             document = existing_document
#         else:
#             print(f"Document does not exist, creating new document")
#             document = await sync_to_async(DocumentMetadata.objects.create)(
#                 file_name=file_data['file_name'],
#                 url=file_data['file_url']
#             )
#             print(f"Document created with ID: {document.id}")
        
#         doc_id = str(document.id)
#         print(f"[_process_single_document] Document record loaded with ID: {doc_id}")
    
    
    

#         # Initialize document processor
#         print("[_process_single_document] Initialize document processor")
#         doc_processor = DocumentProcessor(
#             document_id=doc_id,
#             document_url=file_data['file_url']
#         )

#         print("[_process_single_document] Document processor initialized results: ", doc_processor)

#         sections, reference_data = await sync_to_async(doc_processor.process_document_from_url)(
#             file_data['file_url']
#         )

#         print("[_process_single_document] section data received")
#         print(f"[_process_single_document] Processed {len(sections)} sections")
#         print(f"[_process_single_document] Reference data: {reference_data}")
#         print(x)

#         first_page_text = next(
#             (section['content']['text'] for section in sections if section['content']['type'] == 'title'),
#             sections[0]['content']['text']
#         )
#         metadata = await sync_to_async(summarizer.generate_summary)(
#             first_page_text,
#             doc_id  
#         )
#         print(f"[_process_single_document] Generated metadata for document")
#         summary = metadata['summary']
#         print(f"[_process_single_document] Document Metadata Summary:\n {summary}")
        
#         # Update document with metadata
        
#         cached_data = await sync_to_async(self.cache_manager.get_document_data_sync)(doc_id)
#         print(f"[_process_single_document] Cached data:{doc_id}")
#         if not cached_data:
#             print("[_process_single_document] Not Using cached document metadata")
#             for field, value in metadata.items():
#                 print(f"[_process_single_document] Updating document field: {field} - value: {value}")
#                 setattr(document, field, value)
#             await sync_to_async(document.save)()

        
#         if not cached_data:
#             print("[_process_single_document] Not using cached document section data")
#             # print(f"[_process_single_document] Adding sections")
#             # print(f"\n [_process_single_document] Section data all: \n", sections[4])
#             for section_data in sections:
#                 print(f" [_process_single_document] Each Section data")
#                 print(f"[_process_single_document] Section Type: {section_data['content']['type']}")
#                 section = await sync_to_async(DocumentSection.objects.create)( 
#                     document=document,
#                     section_type=section_data['content']['type'],
#                     content=section_data['content']['text'],
#                     section_start_page_number=section_data['section_start_page_number'],
#                     position=section_data.get('position', 0),
#                     section_id=section_data['section_id'],
#                     start_text=section_data['pointer']['section_start_text'],
#                     url_fragment=f"page={section_data['section_start_page_number']}",
#                     has_citations=bool(section_data['content']['has_citations']),
#                     citations=section_data['citations'],
#                     table_data={},
#                     extracted_image_text={},
#                     # Add new fields
#                     title_group_number=section_data['pointer']['title_group_number'],
#                     title_group_text=section_data['pointer']['title_text'],
#                 )
#                 section.set_elements(section.elements)
#                 print(f"[_process_single_document] Created section: {section.section_id}")


#         # Prepare search sections
#         print("[_process_single_document] Preparing search sections")
#         # print(f"\n [_process_single_document] Section data cite: \n ", sections[4])
#         # print(f"\n [_process_single_document] Section data type: \n ", sections[4]['content']['type'])
#         search_sections = [
#             {
#                 'text': section['content']['text'],
#                 'section_id': section['section_id'],
#                 'page_number': section['section_start_page_number'],
#                 # 'elements': section['elements'],
#                 'section_type': section['content']['type'],
#                 'start_text': section['pointer']['section_start_text'],
#                 'url_fragment': f"page={section['section_start_page_number']}",
#                 'matching_context': "",
#                 'matching_theme': "",
#                 'matching_keywords': [],
#                 'matching_similar_keywords': [],
#                 'relevance_type': [],
#                 'title_group_number': section['pointer'].get('title_group_number'),
#                 'title_group_text': section['pointer'].get('title_text'),
#                 'citations': section['citations'],
#                 'elements': [
#                         {
#                             'text': element.text,
#                             'category': element.category,
#                             'id': element.id
#                         } for element in section['elements']
#                         ] if section['elements'] else [],
#                 } for section in sections
#             ]

#         # Perform search
#         print("[_process_single_document] Searching document - number of sections: ", len(search_sections))
#         search_results = await sync_to_async(searcher.search_document)(
#             search_sections,
#             context,
#             theme,
#             keywords,
#             summary,
#             doc_id,
#             reference_data
#         )
#         print(f"[_process_single_document] Search completed with score: {search_results['relevance_score']}")
       

#         # Update document with search results
#         if not cached_data:
#             print("[_process_single_document] Updating document with search results")
#             last_section = sections[-1]
#             final_page = last_section['section_start_page_number']
#             document.relevance_score = search_results['relevance_score']
#             document.relevant_sections = len(search_results['relevant_sections'])
#             document.total_pages = final_page
#             document.reference = reference_data
#             await sync_to_async(document.save)()


#         response_data = {
#             'document_id': doc_id,
#             'title': document.title,
#             'authors': document.authors,
#             'file_name': file_data['file_name'],
#             'file_url': file_data['file_url'],
#             'file_type': file_data['file_type'],
#             'citation': document.citation,
#             'relevance_score': document.relevance_score,
#             'total_matches': search_results['total_matches'],
#             'relevant_sections': [
#                 {
#                     'section_id': section['section_id'],
#                     'page_number': section['page_number'],
#                     'start_text': section['start_text'],
#                     'url_fragment': section['url_fragment'],
#                     'content': section['text'],
#                     # Add matched content with their corresponding page numbers
#                     'matching_context': section.get('matching_context', ''),
#                     'matching_context_page': section.get('matching_context_page', ''),
#                     'matching_theme': section.get('matching_theme', ''),
#                     'matching_theme_page': section.get('matching_theme_page', ''),
#                     'matching_keywords': section.get('matching_keywords', []),
#                     'matching_keyword_pages': section.get('matching_keyword_pages', [section['page_number']] if section.get('matching_keywords') else []),
#                     'matching_similar_keywords': section.get('matching_similar_keywords', []),
#                     'matching_similar_pages': section.get('matching_similar_pages', [section['page_number']] if section.get('matching_similar_keywords') else []),
#                     'relevance_type': section['relevance_type'],
                    
#                     'matching_context_citations': section['context_citations'],
#                     'matching_theme_citations': section['theme_citations'],
#                     # Add citation and reference data
#                     'citations': section['citations'],
#                     'citation_matches': [
#                         {
#                             'citation_text': citation['text'],
#                             'reference_text': [{ref['text']} for ref in citation['references']] if citation.get('references') else None,
#                             'position': citation.get('position'),
#                             'citation_type': citation.get('type')
#                         }
#                         for citation in section['citations']
#                     ]
#                 }
#                 for section in search_results['relevant_sections']
#             ]
#         }


#         print("[_process_single_document] Returning response")
#         return response_data

#     @action(detail=False, methods=['POST'])
#     def analyze_documents(self, request):
#         return async_to_sync(self._analyze_documents)(request)

#     async def _analyze_documents(self, request):
#         """Async implementation of document analysis"""

#         print("[analyze_documents] Starting document analysis")
#         print(f"[analyze_documents] Request data: {request.data}")

#         # Validate request data
#         data = request.data
#         if not isinstance(data, dict):
#             print("[analyze_documents] ERROR: Invalid request format - expected dictionary")
#             return Response(
#                 {"error": "Invalid request format"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Extract and validate fields
#         files = data.get('files', [])
#         context = data.get('context')
#         theme = data.get('theme')
#         keywords = data.get('keywords', [])

#         # Field validation
#         if not files:
#             print("[analyze_documents] ERROR: No files provided")
#             return Response(
#                 {"error": "No files provided"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         if not context:
#             print("[analyze_documents] ERROR: No context provided")
#             return Response(
#                 {"error": "Context is required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         if not theme:
#             print("[analyze_documents] ERROR: No theme provided")
#             return Response(
#                 {"error": "Theme is required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         print(f"[analyze_documents] Processing {len(files)} files")
#         print(f"[analyze_documents] Context: {context}")
#         print(f"[analyze_documents] Theme: {theme}")
#         print(f"[analyze_documents] Keywords: {keywords}")


#         # Initialize services
#         processor = DocumentProcessor()
#         summarizer = DocumentSummarizer()
#         searcher = DocumentSearcher()


#         # Process documents concurrently
#         tasks = []
#         for file_data in files:
#             if not all(k in file_data for k in ['file_url', 'file_id', 'file_type']):
#                 print(f"[analyze_documents] ERROR: Invalid file data structure: {file_data}")
#                 continue
#             print("[analyze_documents] Processing file:", file_data)
#             task = self._process_single_document(
#                 file_data=file_data,
#                 context=context,
#                 theme=theme,
#                 keywords=keywords,
#                 processor=processor,
#                 summarizer=summarizer,
#                 searcher=searcher
#             )

#             print("[analyze_documents] Processing task:", task)
#             tasks.append(task)

#         if not tasks:
#             print("[analyze_documents] ERROR: No valid files to process")
#             return Response(
#                 {'error': 'No valid files to process'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         results = await asyncio.gather(*tasks, return_exceptions=True)

#         # Process results
#         successful_results = []
#         for idx, result in enumerate(results):
#             if isinstance(result, Exception):
#                 print(f"[analyze_documents] ERROR: Document {idx} failed: {str(result)}")
                
#             else:
#                 successful_results.append(result)

#         if not successful_results:
#             print("[analyze_documents] ERROR: All documents failed processing")
#             return Response(
#                 {
#                     'status': 'error',
#                     'message': 'No documents were processed successfully'
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#         print("[analyze_documents] All documents processed successfully")
#         return Response({
#             'status': 'success',
#             'results': successful_results
#         })





# src/research_assistant/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action 
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async, async_to_sync
import asyncio
from typing import Dict, List
import json

from .models import DocumentMetadata, DocumentSection
from .services.document_processor import DocumentProcessor
from .services.document_summarizer import DocumentSummarizer
from .services.cache_manager import DocumentCacheManager

@method_decorator(csrf_exempt, name='dispatch')
class DocumentManagementViewSet(viewsets.ViewSet):
    """Handle document upload and processing"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache_manager = DocumentCacheManager()
        print("[DocumentManagementViewSet] Initialized")

    async def _process_document(self, file_data: Dict) -> Dict:
        """Process single document and return metadata"""
        print(f"[_process_document] Processing document: {file_data['file_name']}")

        # Create or get document
        document = await sync_to_async(DocumentMetadata.objects.create)(
            file_name=file_data['file_name'],
            url=file_data['file_url'],
            processing_status='processing'
        )

        try:
            # Initialize processors
            doc_processor = DocumentProcessor(
                document_id=str(document.id),
                document_url=file_data['file_url']
            )
            summarizer = DocumentSummarizer()

            # Process document
            sections, reference_data = await sync_to_async(doc_processor.process_document_from_url)(
                file_data['file_url']
            )

            print(f"[_process_document] Processed {len(sections)} sections")

            # Extract metadata from first page - Updated access
            first_page_text = next(
                (section['content']['text'] for section in sections if section['content']['type'] == 'title'),
                sections[0]['content']['text']
            )

            metadata = await sync_to_async(summarizer.generate_summary)(
                first_page_text,
                document.id 
            )

            print(f"[_process_document] Generated metadata for document")

            # Update document with metadata
            for field, value in metadata.items():
                setattr(document, field, value)
            document.reference = reference_data
            document.processing_status = 'completed'
            await sync_to_async(document.save)()
            print(f"[_process_document] Document Saved")
            return {
                'document_id': str(document.id),
                'title': document.title,
                'authors': document.authors,
                'summary': document.summary,
                'references': document.reference,
                'processing_status': document.processing_status,
                'file_name': file_data['file_name'],
                'file_url': file_data['file_url']
            }

        except Exception as e:
            print(f"[_process_document] Error: {str(e)}")
            document.processing_status = 'failed'
            document.error_message = str(e)
            await sync_to_async(document.save)()
            raise

    @action(detail=False, methods=['POST'])
    def upload_documents(self, request):
        """Handle document uploads"""
        return async_to_sync(self._upload_documents)(request)

    async def _upload_documents(self, request):
        """Async implementation of document upload"""
        print("[_upload_documents] Starting document upload")
        
        data = request.data
        if not isinstance(data, list):
            data = [data]

        if not data:
            return Response(
                {"error": "No files provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process documents
        tasks = []
        for file_data in data:
            if not all(k in file_data for k in ['file_url', 'file_id', 'file_type']):
                continue
            task = self._process_document(file_data)
            tasks.append(task)

        if not tasks:
            return Response(
                {'error': 'No valid files to process'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out errors
            successful_results = [
                result for result in results 
                if not isinstance(result, Exception)
            ]

            if not successful_results:
                return Response(
                    {
                        'status': 'error',
                        'message': 'No documents were processed successfully'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response({
                'status': 'success',
                'documents': successful_results
            })

        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['GET'])
    def get_documents(self, request):
        """Retrieve all documents"""
        documents = DocumentMetadata.objects.all().order_by('-created_at')
        
        return Response({
            'status': 'success',
            'documents': [{
                'document_id': str(doc.id),
                'title': doc.title,
                'authors': doc.authors,
                'summary': doc.summary,
                'references': doc.reference,
                'processing_status': doc.processing_status,
                'file_name': doc.file_name,
                'file_url': doc.url
            } for doc in documents]
        })