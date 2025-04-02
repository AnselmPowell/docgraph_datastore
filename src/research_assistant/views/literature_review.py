# src/research_assistant/views/literature_review.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async, async_to_sync
import asyncio
import threading
from threading import Lock
import time
import uuid

from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from ..models import DocumentMetadata, DocumentSection, LiteratureReview
from ..services.literature_extractor import LiteratureExtractor


@method_decorator(csrf_exempt, name='dispatch')
class LiteratureReviewViewSet(viewsets.ViewSet):
    """Handle literature review extraction and retrieval"""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.processing_threads = {}
        self.thread_lock = Lock()
        self.max_concurrent_processes = 2  # Limit concurrent extraction processes

    def _process_literature_review_background(self, document_id, user):
        """Background processing task for literature review extraction"""
        document_id_str = str(document_id)
        
        try:
            print(f"[_process_literature_review_background] Starting extraction for: {document_id}")
            
            # Get the document
            document = DocumentMetadata.objects.get(id=document_id)
            
            # Check if literature review already exists and is completed
            existing_review = LiteratureReview.objects.filter(
                document=document, 
                processing_status='completed'
            ).first()
            
            if existing_review:
                print(f"[_process_literature_review_background] Literature review already exists for: {document_id}")
                with self.thread_lock:
                    if document_id_str in self.processing_threads:
                        del self.processing_threads[document_id_str]
                return
            
            # Create or get pending literature review
            literature_review, created = LiteratureReview.objects.get_or_create(
                document=document,
                user=user,
                defaults={
                    'processing_status': 'processing'
                }
            )
            
            if not created:
                literature_review.processing_status = 'processing'
                literature_review.save()
            
            # Get document sections
            sections = list(DocumentSection.objects.filter(document=document).order_by('section_start_page_number'))
            
            if not sections:
                raise ValueError("Document has no sections to analyze")
            
            # Get reference data
            reference_data = document.reference or {}
            
            # Initialize extractor and process document
            extractor = LiteratureExtractor()
            extraction_result = extractor.extract_literature_review(
                document_id=str(document.id),
                sections=sections,
                reference_data=reference_data
            )
            
            if extraction_result.get('status') == 'success':
                extraction_data = extraction_result.get('extraction_data', {})
                
                # Update literature review with extracted data
                literature_review.research_area = extraction_data.get('research_area', '')
                literature_review.themes = extraction_data.get('themes', [])
                literature_review.chronological_development = extraction_data.get('chronological_development')
                literature_review.theoretical_frameworks = extraction_data.get('theoretical_frameworks')
                literature_review.methodological_approaches = extraction_data.get('methodological_approaches', {})
                literature_review.key_findings = extraction_data.get('key_findings', [])
                literature_review.method_strengths = extraction_data.get('method_strengths', [])
                literature_review.method_limitations = extraction_data.get('method_limitations', [])
                literature_review.result_strengths = extraction_data.get('result_strengths', [])
                literature_review.result_weaknesses = extraction_data.get('result_weaknesses', [])
                literature_review.potential_biases = extraction_data.get('potential_biases', [])
                
                literature_review.extraction_time = extraction_result.get('processing_time', 0)
                literature_review.processing_status = 'completed'
                literature_review.save()
                
                print(f"[_process_literature_review_background] Successfully extracted literature review for: {document_id}")
            else:
                # Update literature review with error
                literature_review.processing_status = 'failed'
                literature_review.error_message = extraction_result.get('error_message', 'Unknown error during extraction')
                literature_review.save()
                
                print(f"[_process_literature_review_background] Failed to extract literature review for: {document_id}")
                
        except Exception as e:
            print(f"[_process_literature_review_background] Error processing literature review: {str(e)}")
            # Update status to failed
            try:
                literature_review = LiteratureReview.objects.get(document_id=document_id)
                literature_review.processing_status = 'failed'
                literature_review.error_message = str(e)
                literature_review.save()
            except Exception as inner_e:
                print(f"[_process_literature_review_background] Failed to update literature review status: {str(inner_e)}")
        finally:
            # Remove the thread from tracking with thread safety
            with self.thread_lock:
                if document_id_str in self.processing_threads:
                    del self.processing_threads[document_id_str]

    @action(detail=False, methods=['POST'])
    def extract(self, request):
        """Extract literature review from a document"""
        document_id = request.data.get('document_id')
        
        if not document_id:
            return Response(
                {'status': 'error', 'message': 'No document ID provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if document exists and belongs to user
            document = DocumentMetadata.objects.get(
                id=document_id,
                user=request.user
            )
            
            # Check if document is processed
            if document.processing_status != 'completed':
                return Response(
                    {'status': 'error', 'message': 'Document processing is not complete'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if literature review already exists
            existing_review = LiteratureReview.objects.filter(
                document=document
            ).first()
            
            if existing_review:
                # If completed, return it
                if existing_review.processing_status == 'completed':
                    return Response({
                        'status': 'success',
                        'message': 'Literature review already extracted',
                        'literature_review_id': str(existing_review.id),
                        'processing_status': existing_review.processing_status
                    })
                # If failed, start a new extraction
                elif existing_review.processing_status == 'failed':
                    existing_review.processing_status = 'pending'
                    existing_review.error_message = None
                    existing_review.save()
                # If pending or processing, return status
                else:
                    return Response({
                        'status': 'success',
                        'message': f'Literature review extraction is {existing_review.processing_status}',
                        'literature_review_id': str(existing_review.id),
                        'processing_status': existing_review.processing_status
                    })
            else:
                # Create new literature review
                with transaction.atomic():
                    existing_review = LiteratureReview.objects.create(
                        id=uuid.uuid4(),
                        document=document,
                        user=request.user,
                        processing_status='pending'
                    )
            
            # Start extraction in background
            document_id_str = str(document.id)
            
            # Check if already processing
            with self.thread_lock:
                if document_id_str in self.processing_threads:
                    return Response({
                        'status': 'success',
                        'message': 'Literature review extraction already in progress',
                        'literature_review_id': str(existing_review.id),
                        'processing_status': 'processing'
                    })
                
                # Check if we're at max capacity
                current_thread_count = len(self.processing_threads)
                
                if current_thread_count >= self.max_concurrent_processes:
                    return Response({
                        'status': 'success',
                        'message': 'Maximum extraction processes reached, please try again later',
                        'literature_review_id': str(existing_review.id),
                        'processing_status': 'pending'
                    }, status=status.HTTP_202_ACCEPTED)
                
                # Create background thread for processing
                thread = threading.Thread(
                    target=self._process_literature_review_background,
                    args=(document.id, request.user)
                )
                thread.daemon = True
                
                # Add to tracking dict with thread safety
                self.processing_threads[document_id_str] = thread
                
                # Start the thread
                thread.start()
            
            return Response({
                'status': 'success',
                'message': 'Literature review extraction started',
                'literature_review_id': str(existing_review.id),
                'processing_status': 'processing'
            })
            
        except DocumentMetadata.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Document not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['GET'])
    def get_review(self, request):
        """Get literature review for a document"""
        document_id = request.query_params.get('document_id')
        
        if not document_id:
            return Response(
                {'status': 'error', 'message': 'No document ID provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if literature review exists
            literature_review = LiteratureReview.objects.filter(
                document_id=document_id,
                user=request.user
            ).first()
            
            if not literature_review:
                return Response(
                    {'status': 'error', 'message': 'Literature review not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Return literature review data
            return Response({
                'status': 'success',
                'literature_review_id': str(literature_review.id),
                'document_id': document_id,
                'processing_status': literature_review.processing_status,
                'error_message': literature_review.error_message,
                'data': {
                    'research_area': literature_review.research_area,
                    'themes': literature_review.themes,
                    'chronological_development': literature_review.chronological_development,
                    'theoretical_frameworks': literature_review.theoretical_frameworks,
                    'methodological_approaches': literature_review.methodological_approaches,
                    'key_findings': literature_review.key_findings,
                    'method_strengths': literature_review.method_strengths,
                    'method_limitations': literature_review.method_limitations,
                    'result_strengths': literature_review.result_strengths,
                    'result_weaknesses': literature_review.result_weaknesses,
                    'potential_biases': literature_review.potential_biases
                }
            })
            
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['POST'], url_path='check-status')
    def check_status(self, request):
        """Check status of literature review extraction"""
        literature_review_id = request.data.get('literature_review_id')
        
        if not literature_review_id:
            return Response(
                {'status': 'error', 'message': 'No literature review ID provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if literature review exists
            literature_review = LiteratureReview.objects.get(
                id=literature_review_id,
                user=request.user
            )
            
            return Response({
                'status': 'success',
                'literature_review_id': str(literature_review.id),
                'document_id': str(literature_review.document.id),
                'processing_status': literature_review.processing_status,
                'error_message': literature_review.error_message
            })
            
        except LiteratureReview.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Literature review not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )