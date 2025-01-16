# # research_assistant/urls.py


from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentManagementViewSet, DocumentSearchViewSet

router = DefaultRouter()
router.register(r'documents', DocumentManagementViewSet, basename='documents')
router.register(r'search', DocumentSearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
    path('documents/upload/', 
         DocumentManagementViewSet.as_view({'post': 'upload_documents'}), 
         name='upload-documents'),
    path('documents/search/',
         DocumentSearchViewSet.as_view({'post': 'search'}),
         name='search-documents'),
    path('documents/list/',
         DocumentManagementViewSet.as_view({'get': 'get_documents'}),
         name='list-documents'),
     path('documents/delete',  # Correct URL
         DocumentManagementViewSet.as_view({'delete': 'delete_documents'}),
         name='delete-documents'),
     ]

