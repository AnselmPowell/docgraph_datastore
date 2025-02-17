# # # research_assistant/urls.py


# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import DocumentManagementViewSet, DocumentSearchViewSet

# router = DefaultRouter()
# router.register(r'documents', DocumentManagementViewSet, basename='documents')
# router.register(r'search', DocumentSearchViewSet, basename='search')

# urlpatterns = [
#     path('', include(router.urls)),
#     path('documents/upload/', 
#          DocumentManagementViewSet.as_view({'post': 'upload_documents'}), 
#          name='upload-documents'),
#     path('documents/search/',
#          DocumentSearchViewSet.as_view({'post': 'search'}),
#          name='search-documents'),
#     path('documents/list/',
#          DocumentManagementViewSet.as_view({'get': 'get_documents'}),
#          name='list-documents'),
#      path('documents/delete', 
#          DocumentManagementViewSet.as_view({'delete': 'delete_documents'}),
#          name='delete-documents-no-slash'),
#      ]




# research_assistant/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentManagementViewSet, DocumentSearchViewSet
from rest_framework.permissions import IsAuthenticated

# Initialize router
router = DefaultRouter()
router.register(r'documents', DocumentManagementViewSet, basename='documents')
router.register(r'search', DocumentSearchViewSet, basename='search')

# Define URL patterns
urlpatterns = [
    # Include router URLs (these inherit authentication from the viewsets)
    path('', include(router.urls)),
    
    # Explicit routes with authentication
    path('documents/upload/',
         DocumentManagementViewSet.as_view(
             {'post': 'upload_documents'},
             permission_classes=[IsAuthenticated]
         ),
         name='upload-documents'),
         
    path('documents/list/',
         DocumentManagementViewSet.as_view(
             {'get': 'get_documents'},
             permission_classes=[IsAuthenticated]
         ),
         name='list-documents'),

    path('documents/delete',
         DocumentManagementViewSet.as_view(
             {'delete': 'delete_documents'},
             permission_classes=[IsAuthenticated]
         ),
         name='delete-documents-no-slash'),
    
    path('documents/search/',
         DocumentSearchViewSet.as_view({
             'post': 'search_results',
             'get': 'get_search_results',  # Add this line
             'delete': 'remove_search_result'  # Add this line
         }, permission_classes=[IsAuthenticated]),
         name='search-documents'),  
]
