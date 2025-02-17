# # src/research_assistant/views/document_search.py

# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from django.views.decorators.csrf import csrf_exempt 
# from django.utils.decorators import method_decorator
# from asgiref.sync import sync_to_async, async_to_sync
# from typing import Dict, List, Optional
# import asyncio

# from ..models import DocumentMetadata 
# from ..services.search.search_manager import SearchManager



# # src/research_assistant/views/document_search.py
# @method_decorator(csrf_exempt, name='dispatch')
# class DocumentSearchViewSet(viewsets.ViewSet):
#     """Handle document search requests"""
    
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.search_manager = SearchManager()
#         print("[DocumentSearchViewSet] Initialized")

#     @action(detail=False, methods=['POST'])
#     def search(self, request):
#         """Handle document search requests
        
#         Input:
#             request.data: {
#                 document_ids: List[str],
#                 context: str,
#                 keywords: List[str]
#             }
#         """
#         return async_to_sync(self._handle_search)(request)

#     async def _handle_search(self, request):
#         """Async implementation of search handler"""
#         print("inside search handle")
#         data = request.data
#         if not isinstance(data, dict):
#             data = {'file_name': data}  # Handle different input formats
        
#         file_name = data.get('file_name')
#         if isinstance(file_name, list):
#             file_name = file_name[0] 
        
#         print("Extract and validate fields:", data)
#         # Extract and validate fields
#         file_name = data.get('file_name', [])
#         context = data.get('context')
#         keywords = data.get('keywords', [])
        
#         print("has document file name:", file_name)
#         if not file_name:
#             return Response(
#                 {"error": "No documents selected"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
    
#         print("has document context")
#         if not context:
#             return Response(
#                 {"error": "Search context is required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         print(f"[_handle_search] Searching {file_name} documents")
#         print(f"[_handle_search] Context: {context}")
#         print(f"[_handle_search] Keywords: {keywords}")

#         # Perform search directly
#         results = await sync_to_async(self.search_manager.search_documents)(
#             documents=data,
#             context=context,
#             keywords=keywords
#         )

#         return Response(results)

#     # except Exception as e:
#     #     print(f"[_handle_search] Error: {str(e)}")
#     #     return Response(
#     #         {'status': 'error', 'message': str(e)},
#     #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
#     #     )










# # src/research_assistant/views/document_search.py

# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from django.views.decorators.csrf import csrf_exempt 
# from django.utils.decorators import method_decorator
# from asgiref.sync import sync_to_async, async_to_sync

# from typing import Dict, List, Optional

# from ..models import SearchResult
# from ..services.search.search_manager import SearchManager, DocumentMetadata

# from rest_framework.permissions import IsAuthenticated


# def get_document_sync(document_id):
#         """Fetch document metadata synchronously"""
#         return DocumentMetadata.objects.get(id=document_id)

# # src/research_assistant/views/document_search.py
# @method_decorator(csrf_exempt, name='dispatch')
# class DocumentSearchViewSet(viewsets.ViewSet):
#     """Handle document search requests"""
#     permission_classes = [IsAuthenticated]
    
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.search_manager = SearchManager()
#         print("[DocumentSearchViewSet] Initialized")

#     @action(detail=False, methods=['POST'])
#     def search(self, request):
#         """Handle document search requests
        
#         Input:
#             request.data: {
#                 document_ids: List[str],
#                 context: str,
#                 keywords: List[str]
#             }
#         """
#         return async_to_sync(self._handle_search)(request)
    

#     async def _handle_search(self, request):
#         print(f"[_handle_search] Starting search for email: {request.user.email}")

#         data = request.data
#         if not isinstance(data, dict):
#             data = {'file_name': data}

#         data['user'] = request.user
        
#         file_name = data.get('file_name')
#         if isinstance(file_name, list):
#             file_name = file_name[0] 
            
        
        
#         print("Extract and validate fields:", data)
#         # Extract and validate fields
#         file_name = data.get('file_name', [])
#         context = data.get('context')
#         keywords = data.get('keywords', []) 
        
#         print("has document file name:", file_name)
#         if not file_name:
#             return Response({
#                 'status': 'error',
#                 'message': 'No documents selected',
#                 'detail': 'Please select at least one document to search'
#             }, status=status.HTTP_400_BAD_REQUEST)
    
#         print("has document context")
#         if not context:
#             return Response({
#                 'status': 'error',
#                 'message': 'Search context required',
#                 'detail': 'Please provide search terms or context'
#             }, status=status.HTTP_400_BAD_REQUEST)

#         print(f"[_handle_search] Searching {file_name} documents")
#         print(f"[_handle_search] Context: {context}")
#         print(f"[_handle_search] Keywords: {keywords}")

#         try:
#             results = await sync_to_async(self.search_manager.search_documents)(
#                 documents=data,
#                 context=context,
#                 keywords=keywords,
#                 user=request.user
#             )

#             # Save search results
#             for result in results.get('results', []):
#                 document = await DocumentMetadata.objects.get(
#                         id=result['document_id']
#                     )
#                 # document = await sync_to_async(get_document_sync, thread_sensitive=True)(result['document_id'])
               
#                 SearchResult.objects.create(
#                     user=request.user,
#                     document=document,
#                     query_context=context,
#                     keywords=keywords,
#                     document_title=result['title'],
#                     document_authors=result['authors'],
#                     document_summary=result['summary'],
#                     relevance_score=result['relevance_score'],
#                     matching_sections=result['matching_sections']
#                 )

#                 return Response(results)
#         except Exception as e:
#             print(f"[Search] Error performing search: {str(e)}")
#             return Response({
#                 'status': 'error',
#                 'message': 'Search failed',
#                 'detail': 'Unable to complete search. Please try again'
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        

#     def get_search_results(self, request):
#         """Retrieve search results for user"""
#         print(f"[get_search_results] Fetching results for user: {request.user.email}")
        
#         try:
#             results = SearchResult.objects.filter(
#                 user=request.user
#             ).order_by('-created_at')
            
#             formatted_results = []
#             for result in results:
#                 formatted_result = {
#                     'document_id': str(result.document.id),
#                     'title': result.document_title,
#                     'question': result.query_context,
#                     'keywords': result.keywords,
#                     'authors': result.document_authors,
#                     'summary': result.document_summary,
#                     'relevance_score': result.relevance_score,
#                     'matching_sections': result.matching_sections
#                 }
#                 formatted_results.append(formatted_result)
            
#             print(f"[get_search_results] Found {len(formatted_results)} results")
            
#             return Response({
#                 'status': 'success',
#                 'results': formatted_results,
#                 'total_matches': len(formatted_results)
#             })
                
#         except Exception as e:
#             print(f"[get_search_results] Error: {str(e)}")
#             return Response({
#                 'status': 'error',
#                 'message': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# src/research_assistant/views/document_search.py

from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt 
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async
from django.db import transaction
import asyncio

from ..models import SearchResult, DocumentMetadata
from ..services.search.search_manager import SearchManager

@method_decorator(csrf_exempt, name='dispatch')
class DocumentSearchViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_manager = SearchManager()
        print("[DocumentSearchViewSet] Initialized")

    @action(detail=False, methods=['POST'])
    def search_results(self, request):
        # Use synchronous wrapper for async function
        return asyncio.run(self._handle_search(request))

    async def _handle_search(self, request):
        print(f"[_handle_search] Starting search for email: {request.user.email}")
        data  = request.data
        context = data.get('context')
        keywords = data.get('keywords', [])

        try:
            # Validate input data
            data = self._prepare_search_data(request)
            print("Search Results: retured")

            # Perform search using sync_to_async
            print("Search Results: Init search manager ")
            search_func = sync_to_async(self.search_manager.search_documents)

            results = await search_func(
                search_data=data,
                context=context,
                keywords=keywords,
                user=request.user
            )
            print("Save Search ")
            # Save results using sync_to_async with transaction
            await self._save_search_results(request.user, context, 
                                         keywords, results)

            return Response(results)

        except Exception as e:
            print(f"[Search] Error performing search: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Search failed',
                'detail': 'Unable to complete search. Please try again'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _prepare_search_data(self, request):
        """Prepare and validate search data"""
        print("[Prepare Search] Prepare and validate search data")
        data = request.data
        if not isinstance(data, dict):
            data = {'file_name': data}

        print("[Prepare Search] Search data: ", data)
        data['user'] = request.user
        
        file_names = data.get('file_name')
        # if isinstance(file_name, list):
        #     file_name = file_name[0]

        searchResults = []
        for file_name in file_names:  

            context = data.get('context')
            keywords = data.get('keywords', [])
            
            searchResults.append({
                'file_name': file_name,
                'context': context,
                'keywords': keywords,
                'user': request.user
            })
        print("[prepare_search]  Done Preparing:", searchResults)
        return searchResults

    @sync_to_async
    def _save_search_results(self, user, context, keywords, results):
        """Save search results with transaction"""
       
        with transaction.atomic():
            for result in results.get('results', []):
                document = DocumentMetadata.objects.get(id=result['document_id'])
                print("Matching Section Results: \n", result['matching_sections'])
                SearchResult.objects.create(
                    id=result['search_results_id'],
                    user=user,
                    document=document,
                    query_context=context,
                    keywords=keywords,
                    document_title=result['title'],
                    document_authors=result['authors'],
                    document_summary=result['summary'],
                    relevance_score=result['relevance_score'],
                    matching_sections=result['matching_sections']
                )

    @action(detail=False, methods=['GET'])
    def get_search_results(self, request):
        """Retrieve search results for user synchronously"""
        print(f"[get_search_results] Fetching results for user: {request.user.email}")
        
        try:
            results = SearchResult.objects.filter(
                user=request.user
            ).order_by('-created_at')
            
            formatted_results = []
            for result in results:
                formatted_result = {
                    'search_results_id': result.id,
                    'document_id': str(result.document.id),
                    'title': result.document_title,
                    'question': result.query_context,
                    'keywords': result.keywords,
                    'authors': result.document_authors,
                    'summary': result.document_summary,
                    'relevance_score': result.relevance_score,
                    'matching_sections': result.matching_sections
                }
                formatted_results.append(formatted_result)
            
            return Response({
                'status': 'success',
                'results': formatted_results,
                'total_matches': len(formatted_results)
            })
                
        except Exception as e:
            print(f"[get_search_results] Error: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


    @action(detail=False, methods=['DELETE'])
    def remove_search_result(self, request):
        """Remove a specific search result"""
        print("[remove_search_result] Starting removal")
        
        try:
            search_result_id = request.data.get('search_result_id')
            
            if not search_result_id:
                return Response({
                    'status': 'error',
                    'message': 'No search result ID provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            

            # Get the search result and verify ownership
            try:
                search_result = SearchResult.objects.get(
                    id=search_result_id,
                    user=request.user
                )
            except SearchResult.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Search result not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Delete the search result
            search_result.delete()
            print(f"[remove_search_result] Successfully removed result: {search_result_id}")

            return Response({
                'status': 'success',
                'message': 'Search result removed successfully'
            })

        except Exception as e:
            print(f"[remove_search_result] Error: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to remove search result'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
