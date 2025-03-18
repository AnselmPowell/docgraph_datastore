
# # research_assistant/urls.py

# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import DocumentManagementViewSet, DocumentSearchViewSet
# from rest_framework.permissions import IsAuthenticated

# # Initialize router
# router = DefaultRouter()
# router.register(r'documents', DocumentManagementViewSet, basename='documents')
# router.register(r'search', DocumentSearchViewSet, basename='search')

# # Define URL patterns
# urlpatterns = [
#     # Include router URLs (these inherit authentication from the viewsets)
#     path('', include(router.urls)),
    
#     # Explicit routes with authentication
#     path('documents/upload/',
#          DocumentManagementViewSet.as_view(
#              {'post': 'upload_documents'},
#              permission_classes=[IsAuthenticated]
#          ),
#          name='upload-documents'),
         
#     path('documents/list/',
#          DocumentManagementViewSet.as_view(
#              {'get': 'get_documents'},
#              permission_classes=[IsAuthenticated]
#          ),
#          name='list-documents'),

#     path('documents/delete',
#          DocumentManagementViewSet.as_view(
#              {'delete': 'delete_documents'},
#              permission_classes=[IsAuthenticated]
#          ),
#          name='delete-documents-no-slash'),
    
#     path('documents/search/',
#          DocumentSearchViewSet.as_view({
#              'post': 'search_results',
#              'get': 'get_search_results',  # Add this line
#              'delete': 'remove_search_result'  # Add this line
#          }, permission_classes=[IsAuthenticated]),
#          name='search-documents'),  
# ]



# research_assistant/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentManagementViewSet, DocumentSearchViewSet, NoteManagerViewSet
from rest_framework.permissions import IsAuthenticated

# Initialize router
router = DefaultRouter()
router.register(r'documents', DocumentManagementViewSet, basename='documents')
router.register(r'search', DocumentSearchViewSet, basename='search')
router.register(r'notes', NoteManagerViewSet, basename='notes')

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
             'get': 'get_search_results',
             'delete': 'remove_search_result'
         }, permission_classes=[IsAuthenticated]),
         name='search-documents'),
         
   
    path('documents/search/check-status/',
         DocumentSearchViewSet.as_view({
             'post': 'check_search_status'
         }, permission_classes=[IsAuthenticated]),
         name='check-search-status'),

         path('notes/',
         NoteManagerViewSet.as_view({
             'get': 'list',
             'post': 'create'
         }, permission_classes=[IsAuthenticated]),
         name='notes-list-create'),
         
    path('notes/<str:pk>/',
         NoteManagerViewSet.as_view({
             'delete': 'destroy'
         }, permission_classes=[IsAuthenticated]),
         name='notes-detail'),
]