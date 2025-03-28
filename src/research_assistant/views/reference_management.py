# src/research_assistant/views/reference_management.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated

from ..models import DocumentMetadata
from ..services.reference_extractor import ReferenceExtractor

@method_decorator(csrf_exempt, name='dispatch')
class ReferenceManagementViewSet(viewsets.ViewSet):
    """Handle reference list management"""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reference_extractor = ReferenceExtractor()
    
    @action(detail=False, methods=['POST'])
    def update_references(self, request):
        """Update document references from pasted reference list"""
        print("BEGIN REFERENCE UPLOAD")
        document_id = request.data.get('document_id')
        reference_text = request.data.get('reference_text')
        print("REF DOCUMNET ID:", document_id)
        if not document_id or not reference_text:
            return Response({
                'status': 'error',
                'message': 'Missing required fields',
                'detail': 'Both document_id and reference_text are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        

        try:
            print("Verify document ownership and existence")
            document = DocumentMetadata.objects.get(
                id=document_id,
                user=request.user
            )
            
            print(" Extract references from pasted text")
            references = self.reference_extractor.extract_references(reference_text)
            
            print("Update document references")
            # If document already has references, merge them
            if document.reference and 'entries' in document.reference:
                # Create a new dictionary to avoid modifying the existing one directly
                updated_references = {
                    'entries': {**references.get('entries', {})},
                    'type': 'manual',
                    'start_page': document.reference.get('start_page'),
                    'end_page': document.reference.get('end_page')
                }
                document.reference = updated_references
            else:
                document.reference = references
            
            print("SAVE DOCUMENT REFERENCE")
            document.save()
            
            print("RETURN REFERENCE LIST ")
            return Response({
                'status': 'success',
                'message': 'References updated successfully',
                'references': document.reference
            })
            
        except DocumentMetadata.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Document not found',
                'detail': 'The requested document could not be found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Failed to update references',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)