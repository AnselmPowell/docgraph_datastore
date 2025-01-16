# src/research_assistant/views/document_management.py

from rest_framework import viewsets, status
from rest_framework.decorators import action 
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async, async_to_sync
import asyncio
from typing import Dict, List, Optional 
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from ..models import DocumentMetadata, DocumentSection
from ..services.document_processor import DocumentProcessor
from ..services.document_summarizer import DocumentSummarizer
from ..services.cache_manager import DocumentCacheManager

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

        # Check for existing document
        existing_doc = await sync_to_async(self.cache_manager.check_existing_document)(file_data)
        if existing_doc:
            print(f"[_process_document] Found existing document: {existing_doc.id}")
            cached_data = await sync_to_async(self.cache_manager.get_document_data_sync)(
                str(existing_doc.id)
            )
            if cached_data:
                return cached_data['document']

        # Create new document if no cache found
        print(f"[_process_document] Creating new document: {file_data['file_name']}")
        document = await sync_to_async(DocumentMetadata.objects.create)(
            file_name=file_data['file_name'],
            url=file_data['file_url'],
            processing_status='processing',
            # metadata={'document_hash': self.cache_manager._generate_document_hash(
            #     file_data['file_name'],
            # )}
        )

        # try:
        # Initialize processors
        doc_processor = DocumentProcessor(
            document_id=str(document.id),
            document_url=file_data['file_url']
        )

        print(f"[_process_document] Initialized document summarizer")
        summarizer = DocumentSummarizer()
       
        # Process document
        print(f"[_process_document] Processing document: {file_data['file_name']}")
        sections, reference_data = await sync_to_async(doc_processor.process_document_from_url)(
            file_data['file_url']
        )

        print(f"[_process_document] Processed {len(sections)} sections")

        # Extract metadata from first page
        print(f"[_process_document] Extracting metadata from first page for summary")
        first_page_text = next(
            (section['content']['text'] for section in sections if section['content']['type'] == 'title'),
            sections[0]['content']['text']
        )

        metadata = await sync_to_async(summarizer.generate_summary)(
            first_page_text,
            document.id 
        )

        print(f"[_process_document] Extracted metadata: {metadata}")

        # Update document with metadata
        for field, value in metadata.items():
            setattr(document, field, value)

        document.reference = reference_data
        print(f"[_process_document] Updated document reference data")
        document.processing_status = 'completed'
        print(f"[_process_document] Document processing complete")
        await sync_to_async(document.save)()

        print(f"[_process_document] Saved document metadata")
        

        # Store sections
        for section_data in sections:
            try:
                section = await sync_to_async(DocumentSection.objects.create)(
                    document=document,
                    section_type=section_data['content']['type'],
                    content=section_data['content']['text'],
                    section_start_page_number=section_data['section_start_page_number'],
                    position=section_data.get('position', 0),
                    section_id=section_data['section_id'],
                    start_text=section_data['pointer']['section_start_text'],
                    url_fragment=f"page={section_data['section_start_page_number']}",
                    has_citations=bool(section_data['content']['has_citations']),
                    citations=section_data['citations'],
                    table_data={},
                    title_group_number=section_data['pointer']['title_group_number'],
                    title_group_text=section_data['pointer']['title_text']
                )

                if 'elements' in section_data:
                    section.set_elements(section_data['elements'])
                    await sync_to_async(section.save)()

            except Exception as e:
                print(f"[_process_document] Error creating section: {str(e)}")
                continue

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

        # except Exception as e:
        #     print(f"[_process_document] Error: {str(e)}")
        #     document.processing_status = 'failed'
        #     document.error_message = str(e)
        #     await sync_to_async(document.save)()
        #     raise


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
        try:
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
                    'file_url': doc.url,
                    'created_at': doc.created_at
                } for doc in documents]
            })
            
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
  
 
    @action(detail=False, methods=['DELETE'])
    def delete_documents(self, request):
        """Delete multiple documents"""
        print("DELETE request received. Data:", request.data)
        """Delete a specific document"""
        try:
            document_id = request.data['document_ids']
            document = get_object_or_404(DocumentMetadata, id=document_id)
            document.delete()
            
            return Response({
                'status': 'success',
                'message': 'Document deleted successfully'
            })
            
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


