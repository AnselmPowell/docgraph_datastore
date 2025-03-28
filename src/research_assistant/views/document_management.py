# src/research_assistant/views/document_management.py

import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action 
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async, async_to_sync
import asyncio
from typing import Dict, List
import logging
from concurrent.futures import ThreadPoolExecutor

import threading
from threading import Lock
import time

from rest_framework.permissions import IsAuthenticated

from ..models import DocumentMetadata, DocumentSection, SearchResult, DocumentRelationship, LLMResponseCache
from ..services.document_processor import DocumentProcessor
from ..services.document_summarizer import DocumentSummarizer



@method_decorator(csrf_exempt, name='dispatch')
class DocumentManagementViewSet(viewsets.ViewSet):
    """Handle document upload and processing"""

    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.processing_threads = {}
        self.thread_lock = Lock()  # Add thread lock for thread safety
        self.max_concurrent_processes = 3  # Limit concurrent processing tasks

    # The _process_document_background method needs this fix to properly handle thread cleanup
    def _process_document_background(self, document_id, file_data, user):
        """Background processing task for a single document"""
        document_id_str = str(document_id)  # Ensure we have string version
        try:
            print(f"[_process_document_background] Starting background processing for: {file_data['file_name']}")
            
            # Get the document
            document = DocumentMetadata.objects.get(id=document_id)
            document.processing_status = 'processing'
            document.save()
            
            # Initialize processors
            doc_processor = DocumentProcessor(
                document_id=file_data["file_id"],
                document_url=file_data['file_url']
            )
            
            # Process document
            sections, reference_data = doc_processor.process_document_from_url(
                file_data['file_url']
            )
            
            summarizer = DocumentSummarizer()
            total_pages = doc_processor.get_total_pages()
            
            # Get metadata
            metadata = summarizer.generate_summary(
                sections[:2],
                document.id
            )
            
            # Update document metadata
            for field, value in metadata.items():
                setattr(document, field, value)
            
            document.reference = reference_data
            document.processing_status = 'completed'
            document.total_pages = total_pages
            document.save()
            
            # Store sections
            for section_data in sections:
                section = DocumentSection.objects.create(
                    document=document,
                    section_type=section_data['content'].get('type', 'text'),
                    content=section_data['content'].get('text', ''),
                    section_start_page_number=int(section_data['section_start_page_number']),
                    prev_page_text=section_data.get('prev_page_text'),
                    next_page_text=section_data.get('next_page_text'),
                    has_citations=bool(section_data['content'].get('has_citations', False)),
                    citations=section_data.get('citations', {})
                )
                
                # Handle tables and images
                if 'elements' in section_data:
                    section.set_elements(section_data['elements'])
                    section.save()
            
            print(f"[_process_document_background] Completed processing document: {document.id}")
            
        except Exception as e:
            print(f"[_process_document_background] Error processing document: {str(e)}")
            # Update document status to failed
            try:
                document = DocumentMetadata.objects.get(id=document_id)
                document.processing_status = 'failed'
                document.error_message = str(e)
                document.save()
            except Exception as inner_e:
                print(f"[_process_document_background] Failed to update document status: {str(inner_e)}")
        finally:
            # Remove the thread from tracking with thread safety
            with self.thread_lock:
                if document_id_str in self.processing_threads:
                    del self.processing_threads[document_id_str]

    # Fix to upload_documents to use proper thread safety
    @action(detail=False, methods=['POST'])
    def upload_documents(self, request):
        """Handle document uploads with immediate response and background processing"""
        data = request.data
        if not isinstance(data, list):
            data = [data]

        if not data:
            return Response(
                {"error": "No files provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Limit to 10 documents at a time
        if len(data) > 10:
            return Response(
                {"error": "Maximum 10 documents allowed per upload"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create pending documents and return immediately
        pending_documents = []
        for file_data in data:
            try:
                # Basic validation
                if not all(k in file_data for k in ['file_url', 'file_id', 'file_type']):
                    continue
                
                # Create pending document
                document = DocumentMetadata.objects.create(
                    user=request.user, 
                    file_name=file_data['file_name'],
                    url=file_data['file_url'],
                    processing_status='pending'
                )
                
                pending_documents.append({
                    'document_id': str(document.id),
                    'title': document.file_name,
                    'authors': [],
                    'pages': 0,
                    'summary': "Document processing...",
                    'citation': "Document processing...",
                    'references': {},
                    'processing_status': 'pending',
                    'file_name': document.file_name,
                    'file_url': document.url,
                    'created_at': document.created_at
                })
                
                # Use thread safety when checking active threads
                with self.thread_lock:
                    current_thread_count = len(self.processing_threads)
                
                # Wait if we're at max capacity
                while current_thread_count >= self.max_concurrent_processes:
                    time.sleep(0.5)
                    with self.thread_lock:
                        current_thread_count = len(self.processing_threads)
                
                # Create background thread for processing
                document_id_str = str(document.id)
                thread = threading.Thread(
                    target=self._process_document_background,
                    args=(document.id, file_data, request.user)
                )
                thread.daemon = True  # Allow thread to exit when main thread exits
                
                # Add to tracking dict with thread safety
                with self.thread_lock:
                    self.processing_threads[document_id_str] = thread
                
                thread.start()
                
            except Exception as e:
                print(f"[upload_documents] Error creating document: {str(e)}")
        
        if not pending_documents:
            return Response(
                {'error': 'No valid files to process'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'status': 'success',
            'documents': pending_documents,
            'message': f"Started processing {len(pending_documents)} documents"
        })
    
    @action(detail=False, methods=['GET'])
    def get_documents(self, request):
        """Retrieve all documents"""
        try:
            # Filter documents by user
            documents = DocumentMetadata.objects.filter(
                user=request.user
            ).order_by('-created_at')

            # Check if documents exist
            if not documents.exists():
                return Response({
                    'status': 'success',
                    'message': 'No documents found',
                    'documents': []
                }, status=status.HTTP_200_OK) 

            return Response({
                'status': 'success',
                'documents': [{
                    'document_id': str(doc.id),
                    'title': doc.title or doc.file_name,
                    'authors': doc.authors or [],
                    'summary': doc.summary,
                    'pages': doc.total_pages or 0,
                    'references': doc.reference or {},
                    'citation': doc.citation,
                    'processing_status': doc.processing_status,
                    'file_name': doc.file_name,
                    'file_url': doc.url,
                    'created_at': doc.created_at,
                    'error_message': doc.error_message
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
  
    # New endpoint to check processing status of specific documents
    @action(detail=False, methods=['POST'], url_path='check-status')
    def check_document_status(self, request):
        """Check processing status of specific documents"""
        document_ids = request.data.get('document_ids', [])
        
        if not document_ids:
            return Response(
                {"error": "No document IDs provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Query documents with the provided IDs
            documents = DocumentMetadata.objects.filter(
                id__in=document_ids,
                user=request.user
            )
            print(documents[0].citation)
            # print(x)
            # Format response
            return Response({
                'status': 'success',
                'documents': [{
                    'document_id': str(doc.id),
                    'title': doc.title or doc.file_name,
                    'authors': doc.authors or [],
                    'summary': doc.summary,
                    'pages': doc.total_pages or 0,
                    'references': doc.reference or {},
                    'citation': doc.citation,
                    'processing_status': doc.processing_status,
                    'file_name': doc.file_name,
                    'file_url': doc.url,
                    'created_at': doc.created_at,
                    'error_message': doc.error_message
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

    # Delete document action remains largely the same
    @action(detail=False, methods=['DELETE'])
    def delete_documents(self, request):
        """Delete document and all related data"""
        try:
            document_id = request.data.get('document_id')

            if not document_id:
                return Response(
                    {"error": "No document ID provided"},
                    status=status.HTTP_400_BAD_REQUEST
                ) 
            
            # Get document and verify ownership
            try:
                document = DocumentMetadata.objects.get(
                    id=document_id,
                    user=request.user
                )
            except DocumentMetadata.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Document not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Cancel any ongoing processing
            if str(document_id) in self.processing_threads:
                # We can't actually kill the thread, but we'll remove it from tracking
                del self.processing_threads[str(document_id)]
            
            # Delete related data
            DocumentSection.objects.filter(document=document).delete()
            SearchResult.objects.filter(document=document).delete()
            LLMResponseCache.objects.filter(document=document).delete()
            DocumentRelationship.objects.filter(source_document=document).delete()
            DocumentRelationship.objects.filter(target_document=document).delete()
            
            # Finally delete the document itself
            document.delete()
            
            return Response({
                'status': 'success',
                'message': 'Document successfully removed',
                'detail': 'Document and associated data have been deleted'
            })
        except DocumentMetadata.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Document not found',
                'detail': 'The requested document could not be found or may have been already deleted'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Unable to delete document',
                'detail': 'Please try again or contact support if the problem persists'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)