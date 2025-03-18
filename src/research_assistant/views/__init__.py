# views/_init_py 

from .document_management import DocumentManagementViewSet
from .document_search import DocumentSearchViewSet
from .note_manager import NoteManagerViewSet
__all__ = ['DocumentManagementViewSet', 'DocumentSearchViewSet', 'NoteManagerViewSet' ]