# src/research_assistant/services/database_cleanup.py
from django.db import transaction
from ..models import DocumentSection, DocumentMetadata

def clear_document_sections():
    """
    Delete all DocumentSection records from the database
    """
    print("[DatabaseCleanup] Starting document sections cleanup")
    
    try:
        with transaction.atomic():
            # Get count before deletion for logging
            count = DocumentSection.objects.count()
            print(f"[DatabaseCleanup] Found {count} sections to delete")
            
            # Delete all sections
            deleted_count = DocumentSection.objects.all().delete()
            print(f"[DatabaseCleanup] Successfully deleted {deleted_count[0]} sections")
            
        return {
            'status': 'success',
            'deleted_count': deleted_count[0]
        }
        
    except Exception as e:
        print(f"[DatabaseCleanup] Error cleaning document sections: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


def clear_document_sections_by_id(document_id):
    """
    Delete all DocumentSection records for a specific document ID
    
    Args:
        document_id (str): UUID of the document to clean up sections for
        
    Returns:
        dict: Status of the cleanup operation including count of deleted sections
    """
    print(f"[DatabaseCleanup] Starting cleanup for document ID: {document_id}")
    
    try:
        with transaction.atomic():
            # Verify document exists
            if not DocumentMetadata.objects.filter(id=document_id).exists():
                return {
                    'status': 'error',
                    'error': f'Document with ID {document_id} not found'
                }
            
            # Get count before deletion for logging
            count = DocumentSection.objects.filter(document_id=document_id).count()
            print(f"[DatabaseCleanup] Found {count} sections to delete for document {document_id}")
            
            # Delete sections for specific document
            deleted_count = DocumentSection.objects.filter(document_id=document_id).delete()
            print(f"[DatabaseCleanup] Successfully deleted {deleted_count[0]} sections for document {document_id}")
            
            return {
                'status': 'success',
                'document_id': document_id,
                'deleted_count': deleted_count[0]
            }
            
    except Exception as e:
        print(f"[DatabaseCleanup] Error cleaning document sections: {str(e)}")
        return {
            'status': 'error',
            'document_id': document_id,
            'error': str(e)
        }