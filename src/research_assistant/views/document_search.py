

# src/research_assistant/views/document_search.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt 
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async, async_to_sync
from typing import Dict, List, Optional
import asyncio

from ..models import DocumentMetadata 
from ..services.search.search_manager import SearchManager
from ..services.cache_manager import DocumentCacheManager

@method_decorator(csrf_exempt, name='dispatch')
class DocumentSearchViewSet(viewsets.ViewSet):
    """Handle document search requests"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_manager = SearchManager()
        self.cache_manager = DocumentCacheManager()
        print("[DocumentSearchViewSet] Initialized")

    @action(detail=False, methods=['POST'])
    def search(self, request):
        """Handle document search requests"""
        return async_to_sync(self._handle_search)(request)

    async def _handle_search(self, request):
        """Async implementation of search handler"""
        try:
            # Validate request data
            data = request.data
            if not isinstance(data, dict):
                return Response(
                    {"error": "Invalid request format"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract and validate required fields
            document_ids = data.get('document_ids', [])
            context = data.get('context')
            theme = data.get('theme')
            keywords = data.get('keywords', [])

            # Validation checks
            if not document_ids:
                return Response(
                    {"error": "No documents selected"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not context:
                return Response(
                    {"error": "Search context is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not theme:
                return Response(
                    {"error": "Theme is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )


            print(f"[_handle_search] Searching {len(document_ids)} documents")
            print(f"[_handle_search] Context: {context}")
            print(f"[_handle_search] Theme: {theme}")
            print(f"[_handle_search] Keywords: {len(keywords)}")

            # try:
            # Check cache first
            print("[_handle_search] Checking cache")
            cached_results = await sync_to_async(self.cache_manager.get_search_cache_sync)(
                document_ids=document_ids,
                context=context,
                theme=theme,
                keywords=keywords
            )

            if cached_results:
                print("[_handle_search] Using cached results")
                return Response(cached_results)

            # Perform new search
            print("[_handle_search] No cache found, performing search")
            results = await sync_to_async(self.search_manager.search_documents)(
                document_ids=document_ids,
                context=context,
                theme=theme,
                keywords=keywords
            )

            # Cache the results
            await sync_to_async(self.cache_manager.store_search_cache_sync)(
                document_ids=document_ids,
                context=context,
                theme=theme,
                keywords=keywords,
                results=results
            )

            return Response(results)

            # except ValueError as e:
            #     print(f"[_handle_search] Validation error: {str(e)}")
            #     return Response(
            #         {'error': str(e)},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )

        except Exception as e:
            print(f"[_handle_search] Error: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['GET'])
    async def get_search_history(self, request):
        """Get search history for documents"""
        try:
            document_ids = request.query_params.getlist('document_ids[]')
            
            if not document_ids:
                return Response(
                    {"error": "No documents specified"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get cached searches for documents
            cached_searches = await sync_to_async(
                LLMResponseCache.objects.filter(
                    document_id__in=document_ids,
                    response_type='search'
                ).order_by('-created_at')
            )()

            # Format response
            history = []
            for cache in cached_searches:
                try:
                    # Only include successful searches
                    if cache.response_data.get('status') == 'success':
                        history.append({
                            'document_id': cache.document_id,
                            'query_hash': cache.query_hash,
                            'created_at': cache.created_at,
                            'result_count': len(cache.response_data.get('results', [])),
                            'relevance_score': cache.response_data.get('relevance_score')
                        })
                except Exception as e:
                    print(f"[get_search_history] Error processing cache entry: {str(e)}")
                    continue

            return Response({
                'status': 'success',
                'history': history
            })

        except Exception as e:
            print(f"[get_search_history] Error: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )