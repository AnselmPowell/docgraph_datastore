# src/research_assistant/views/document_management.py

# document_management.py
from rest_framework import viewsets, status
from rest_framework.decorators import action 
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async, async_to_sync
import asyncio
from typing import Dict, List, Optional 
from django.shortcuts import get_object_or_404
import uuid

from ..models import DocumentMetadata, DocumentSection, SearchResult, DocumentRelationship, LLMResponseCache
from ..services.document_processor import DocumentProcessor
from ..services.document_summarizer import DocumentSummarizer


@method_decorator(csrf_exempt, name='dispatch')
class DocumentManagementViewSet(viewsets.ViewSet):
    """Handle document upload and processing"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
       
        print("[DocumentManagementViewSet] Initialized")

    async def _process_document(self, file_data: Dict) -> Dict:
        """Process single document and return metadata"""
        print(f"[_process_document] Processing document: {file_data['file_name']}")

       # Check for existing document using model query
        existing_doc = await sync_to_async(DocumentMetadata.objects.filter(
            file_name=file_data['file_name'],
            url=file_data['file_url']
        ).first)()

        if existing_doc:
            return {
                'document_id': str(existing_doc.id),
                'title': existing_doc.title,
                'authors': existing_doc.authors,
                'pages': existing_doc.total_pages, 
                'summary': existing_doc.summary,
                'references': existing_doc.reference,
                'processing_status': existing_doc.processing_status,
                'file_name': existing_doc.file_name,
                'file_url': existing_doc.url,
                'created_at': existing_doc.created_at 
            }
        
        # Initialize processors
        doc_processor = DocumentProcessor(
            document_id=file_data["file_id"],
            document_url=file_data['file_url']
        )
        
        # Process document
        print(f"[_process_document] Processing document: {file_data['file_name']}")
        sections, reference_data = await sync_to_async(doc_processor.process_document_from_url)(
            file_data['file_url']
        )

        # Create new document
        print(f"[_process_document] Creating new document: {file_data['file_name']}")
        document = await sync_to_async(DocumentMetadata.objects.create)(
            id=file_data['file_id'],
            file_name=file_data['file_name'],
            url=file_data['file_url'],
            processing_status='processing'
        )
    

        try:
            
            summarizer = DocumentSummarizer()
            
           
            total_pages = await sync_to_async(doc_processor.get_total_pages)()
            print(f"[_process_document] Total Pages {total_pages}")
            print(f"[_process_document] Processed {len(sections)} sections")

            # Get metadata
            metadata = await sync_to_async(summarizer.generate_summary)(
                sections[:2],  # Pass first two sections instead of just first page text
                document.id 
            )

            # Update document metadata
            for field, value in metadata.items():
                setattr(document, field, value)
            document.reference = reference_data
            document.processing_status = 'completed'
            await sync_to_async(document.save)()

            # Store sections
            for section_data in sections:
                try:
                    section = await sync_to_async(DocumentSection.objects.create)(
                        document=document,
                        section_type=section_data['content'].get('type', 'text'),  # Added default
                        content=section_data['content'].get('text', ''),  # Added safety
                        section_start_page_number=int(section_data['section_start_page_number']),  # Ensure int
                        prev_page_text=section_data.get('prev_page_text'),
                        next_page_text=section_data.get('next_page_text'),
                        has_citations=bool(section_data['content'].get('has_citations', False)),
                        citations=section_data.get('citations', {})  # Added default
                    )

                    # Handle tables and images
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
                'pages': total_pages,
                'summary': document.summary,
                'references': document.reference,
                'processing_status': document.processing_status,
                'file_name': file_data['file_name'],
                'file_url': file_data['file_url'],
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
        print("[_upload_documents] request data", request.data)
        
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
            # here--
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
        """Delete document and all related data"""
        print("[DELETE] Starting document deletion")
        try:
            document_id = request.data.get('document_id')
            print(f"[DELETE] Attempting to delete document: {document_id}")

            if not document_id:
                return Response(
                    {"error": "No document ID provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the document
            try:
                document = DocumentMetadata.objects.get(id=document_id)
            except DocumentMetadata.DoesNotExist:
                return Response(
                    {"error": "Document not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Delete related data (Django will handle cascade deletion for ForeignKey relationships)
            # But we'll be explicit about some relationships
            
            # Delete document sections
            DocumentSection.objects.filter(document=document).delete()
            
            # Delete search results
            SearchResult.objects.filter(document=document).delete()
            
            # Delete LLM cache responses
            LLMResponseCache.objects.filter(document=document).delete()
            
            # Delete document relationships
            DocumentRelationship.objects.filter(
                source_document=document
            ).delete()
            DocumentRelationship.objects.filter(
                target_document=document
            ).delete()
            
            # Finally delete the document itself
            document.delete()
            
            return Response({
                'status': 'success',
                'message': 'Document and related data deleted successfully'
            })
                
        except Exception as e:
            print(f"[DELETE] Error deleting document: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        