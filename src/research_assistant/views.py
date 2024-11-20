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

from .models import DocumentMetadata, DocumentSection, ProcessingLog, SearchQuery
from .services.document_processor import DocumentProcessor
from .services.document_summarizer import DocumentSummarizer
from .services.document_searcher import DocumentSearcher

from django.db import connection
from research_assistant.models import DocumentSection
from .services.cache_manager import DocumentCacheManager


@method_decorator(csrf_exempt, name='dispatch')
class ResearchAnalysisViewSet(viewsets.ViewSet):
    """Handle document analysis and search requests"""
    
    def __init__(self, **kwargs):
        # super().__init__(**kwargs)
        self.cache_manager = DocumentCacheManager()
        print("[ResearchAnalysisViewSet] Initialized with API Call")

    async def _process_single_document(
        self,
        file_data: Dict,
        context: str,
        theme: str,
        keywords: List[str],
        processor: DocumentProcessor,
        summarizer: DocumentSummarizer,
        searcher: DocumentSearcher
    ) -> Dict:
        """Process a single document and return results"""  
        print("[_process_single_document] Inside process single document ")  
        print(f"[_process_single_document] Processing document: {file_data['file_name']}")
        print(f"[_process_single_document] URL: {file_data['file_url']}")

    
        doc_id = None
        existing_document = await sync_to_async(lambda: DocumentMetadata.objects.filter(
            file_name=file_data['file_name']
        ).first())()

        if existing_document:
            print(f"Document already exists with ID: {existing_document.id}")
            document = existing_document
        else:
            print(f"Document does not exist, creating new document")
            document = await sync_to_async(DocumentMetadata.objects.create)(
                file_name=file_data['file_name'],
                url=file_data['file_url']
            )
            print(f"Document created with ID: {document.id}")
        
        doc_id = str(document.id)
        print(f"[_process_single_document] Document record loaded with ID: {doc_id}")
    
    

        # Initialize document processor
        print("[_process_single_document] Initialize document processor")
        doc_processor = DocumentProcessor(
            document_id=doc_id,
            document_url=file_data['file_url']
        )

        print("[_process_single_document] Document processor initialized results: ", doc_processor)


        sections = await sync_to_async(doc_processor.process_document_from_url)(
            file_data['file_url']
        )
        print(f"[_process_single_document] Processed {len(sections)} sections")


        first_page_text = next(
            (section['content']['text'] for section in sections if section['content']['type'] == 'title'),
            sections[0]['content']['text']
        )
        metadata = await sync_to_async(summarizer.generate_summary)(
            first_page_text,
            doc_id  
        )
        print(f"[_process_single_document] Generated metadata for document")
        summary = metadata['summary']
        print(f"[_process_single_document] Document Metadata Summary:\n {summary}")
        
        # Update document with metadata
        
        cached_data = await sync_to_async(self.cache_manager.get_document_data_sync)(doc_id)
        print(f"[_process_single_document] Cached data:{doc_id} ------ {cached_data}")
        if not cached_data:
            print("[_process_single_document] Not Using cached document metadata")
            for field, value in metadata.items():
                print(f"[_process_single_document] Updating document field: {field} - value: {value}")
                setattr(document, field, value)
            await sync_to_async(document.save)()

        if not cached_data:
            print("[_process_single_document] Not Using cached document section data")
            print(f"[_process_single_document] adding sections")
            print(f"\n [_process_single_document] Section data: \n")
            for section_data in sections:
                print(f" [_process_single_document] Each Section data")
                print(f"[_process_single_document] Section Type: {section_data['content']['type']}")
                section = await sync_to_async(DocumentSection.objects.create)( 
                    document=document,
                    section_type=section_data['content']['type'],
                    content=section_data['content']['text'],
                    page_number=section_data['page_number'],
                    position=section_data.get('position', 0),
                    section_id=section_data['section_id'],
                    start_text=section_data['pointer']['section_start'],
                    url_fragment=f"page={section_data['page_number']}",
                    has_citations=bool(section_data['content']['citations']),
                    citations=section_data['content']['citations'],
                    table_data={},
                    extracted_image_text={},
                    # Add new fields
                    title_group_number=section_data['pointer']['title_group_number'],
                    title_group_text=section_data['pointer']['title_text'],
                )
                print(f"[_process_single_document] Created section: {section.section_id}")


        # Prepare search sections
        print("[_process_single_document] Preparing search sections")
        search_sections = [
            {
                'text': section['content']['text'],
                'section_id': section['section_id'],
                'page_number': section['page_number'],
                'section_type': section['content']['type'],
                'start_text': section['pointer']['section_start'],
                'url_fragment': f"page={section['page_number']}",
                'matching_context': "",
                'matching_theme': "",
                'matching_keywords': [],
                'matching_similar_keywords': [],
                'relevance_type': [],
                'title_group_number': section['pointer'].get('title_group_number'),
                'title_group_text': section['pointer'].get('title_text'),
            }
            for section in sections
        ]

        # Perform search
        print("[_process_single_document] Searching document - number of sections: ", len(search_sections))
        search_results = await sync_to_async(searcher.search_document)(
            search_sections,
            context,
            theme,
            keywords,
            summary,
            doc_id
        )
        print(f"[_process_single_document] Search completed with score: {search_results['relevance_score']}")
       

        # Update document with search results
        print("[_process_single_document] Updating document with search results")
        last_section = sections[-1]
        final_page = last_section['page_number']
        document.relevance_score = search_results['relevance_score']
        document.relevant_sections = len(search_results['relevant_sections'])
        document.total_pages = final_page
        await sync_to_async(document.save)()

        # Store search query
        # print("[_process_single_document] Creating search query")
        # await sync_to_async(SearchQuery.objects.create)(
        #     context=context,
        #     theme=theme,
        #     keywords=keywords,
        #     documents=[document],
        #     total_results=len(search_results['relevant_sections'])
        # )

      

        # Prepare response
        print("[_process_single_document] Preparing response")
        response_data = {
            'document_id': doc_id,
            'title': document.title,
            'authors': document.authors,
            'citation': document.citation,
            'relevance_score': document.relevance_score,
            'total_matches': search_results['total_matches'],
            'relevant_sections': [
                {
                    'section_id': section['section_id'],
                    'page_number': section['page_number'],
                    'start_text': section['start_text'],
                    'url_fragment': section['url_fragment'],
                    'content': section['text'],
                    'matching_context': section['matching_context'],
                    'matching_theme': section['matching_theme'],
                    'matching_keywords': section['matching_keywords'],
                    'matching_similar_keywords': section['matching_similar_keywords'],
                    'relevance_type': section['relevance_type']
                }
                for section in search_results['relevant_sections']
            ]
        }

        print("[_process_single_document] Returning response")
        return response_data

    @action(detail=False, methods=['POST'])
    def analyze_documents(self, request):
        return async_to_sync(self._analyze_documents)(request)

    async def _analyze_documents(self, request):
        """Async implementation of document analysis"""

        print("[analyze_documents] Starting document analysis")
        print(f"[analyze_documents] Request data: {request.data}")

        # Validate request data
        data = request.data
        if not isinstance(data, dict):
            print("[analyze_documents] ERROR: Invalid request format - expected dictionary")
            return Response(
                {"error": "Invalid request format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract and validate fields
        files = data.get('files', [])
        context = data.get('context')
        theme = data.get('theme')
        keywords = data.get('keywords', [])

        # Field validation
        if not files:
            print("[analyze_documents] ERROR: No files provided")
            return Response(
                {"error": "No files provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not context:
            print("[analyze_documents] ERROR: No context provided")
            return Response(
                {"error": "Context is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not theme:
            print("[analyze_documents] ERROR: No theme provided")
            return Response(
                {"error": "Theme is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"[analyze_documents] Processing {len(files)} files")
        print(f"[analyze_documents] Context: {context}")
        print(f"[analyze_documents] Theme: {theme}")
        print(f"[analyze_documents] Keywords: {keywords}")


        # Initialize services
        processor = DocumentProcessor()
        summarizer = DocumentSummarizer()
        searcher = DocumentSearcher()


        # Process documents concurrently
        tasks = []
        for file_data in files:
            if not all(k in file_data for k in ['file_url', 'file_id', 'file_type']):
                print(f"[analyze_documents] ERROR: Invalid file data structure: {file_data}")
                continue
            print("[analyze_documents] Processing file:", file_data)
            task = self._process_single_document(
                file_data=file_data,
                context=context,
                theme=theme,
                keywords=keywords,
                processor=processor,
                summarizer=summarizer,
                searcher=searcher
            )

            print("[analyze_documents] Processing task:", task)
            tasks.append(task)

        if not tasks:
            print("[analyze_documents] ERROR: No valid files to process")
            return Response(
                {'error': 'No valid files to process'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[analyze_documents] ERROR: Document {idx} failed: {str(result)}")
                
            else:
                successful_results.append(result)

        if not successful_results:
            print("[analyze_documents] ERROR: All documents failed processing")
            return Response(
                {
                    'status': 'error',
                    'message': 'No documents were processed successfully'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


        return Response({
            'status': 'success',
            'results': successful_results
        })
