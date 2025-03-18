# src/research_assistant/views/note_manager.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..services.stored_note import NoteService
from ..models import Note

@method_decorator(csrf_exempt, name='dispatch')
class NoteManagerViewSet(viewsets.ViewSet):
    """Handle note creation, retrieval, and deletion"""
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get all notes for the current user"""
        try:
            notes = NoteService.get_notes(request.user)
            
            return Response({
                'status': 'success',
                'notes': notes
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request):
        """Create a new note"""
        try:
            note_data = request.data
            
            if not note_data.get('content'):
                return Response({
                    'status': 'error',
                    'message': 'Note content is required'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            note = NoteService.create_note(request.user, note_data)
            
            return Response({
                'status': 'success',
                'note': note
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, pk=None):
        """Delete a note"""
        try:
            if not pk:
                return Response({
                    'status': 'error',
                    'message': 'Note ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            success = NoteService.delete_note(request.user, pk)
            
            if not success:
                return Response({
                    'status': 'error',
                    'message': 'Note not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
            return Response({
                'status': 'success',
                'message': 'Note deleted successfully'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)