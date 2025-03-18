# src/research_assistant/services/stored_note.py
from datetime import datetime
from ..models import Note, User
from django.db import transaction
import uuid
import logging

logger = logging.getLogger(__name__)

class NoteService:
    """Service for managing stored notes"""
    
    @staticmethod
    def create_note(user, note_data):
        """Create a new note for the user"""
        try:
            with transaction.atomic():
                # Extract data from request
                title = note_data.get('title', 'Untitled Note')
                content = note_data.get('content', '')
                document_id = note_data.get('document_id')
                page_number = note_data.get('pageNumber')
                citations = note_data.get('citations', [])
                source = note_data.get('source')
                
                # Create note
                note = Note.objects.create(
                    user=user,
                    title=title,
                    content=content,
                    document_id=document_id,
                    page_number=page_number,
                    source=source,
                    citations=citations
                )
                
                return {
                    'id': str(note.id),
                    'title': note.title,
                    'content': note.content,
                    'pageNumber': note.page_number,
                    'citations': note.citations,
                    'source': note.source,
                    'timestamp': note.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error creating note: {str(e)}")
            raise
    
    @staticmethod
    def get_notes(user):
        """Get all notes for a user"""
        try:
            notes = Note.objects.filter(user=user)
            
            return [{
                'id': str(note.id),
                'title': note.title,
                'content': note.content,
                'pageNumber': note.page_number,
                'citations': note.citations,
                'source': note.source,
                'timestamp': note.created_at.isoformat()
            } for note in notes]
            
        except Exception as e:
            logger.error(f"Error retrieving notes: {str(e)}")
            raise
    
    @staticmethod
    def delete_note(user, note_id):
        """Delete a note"""
        try:
            note = Note.objects.filter(user=user, id=note_id).first()
            
            if not note:
                return False
                
            note.delete()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting note: {str(e)}")
            raise