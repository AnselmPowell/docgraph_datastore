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



# src/research_assistant/views/document_search.py
@method_decorator(csrf_exempt, name='dispatch')
class DocumentSearchViewSet(viewsets.ViewSet):
    """Handle document search requests"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_manager = SearchManager()
        print("[DocumentSearchViewSet] Initialized")

    @action(detail=False, methods=['POST'])
    def search(self, request):
        """Handle document search requests
        
        Input:
            request.data: {
                document_ids: List[str],
                context: str,
                keywords: List[str]
            }
        """
        return async_to_sync(self._handle_search)(request)

    async def _handle_search(self, request):
        """Async implementation of search handler"""
        print("inside search handle")
        data = request.data
        if not isinstance(data, dict):
            data = {'file_name': data}  # Handle different input formats
        
        file_name = data.get('file_name')
        if isinstance(file_name, list):
            file_name = file_name[0] 
        
        print("Extract and validate fields:", data)
        # Extract and validate fields
        file_name = data.get('file_name', [])
        context = data.get('context')
        keywords = data.get('keywords', [])
        
        print("has document file name:", file_name)
        if not file_name:
            return Response(
                {"error": "No documents selected"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        print("has document context")
        if not context:
            return Response(
                {"error": "Search context is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"[_handle_search] Searching {file_name} documents")
        print(f"[_handle_search] Context: {context}")
        print(f"[_handle_search] Keywords: {keywords}")

        # Perform search directly
        results = await sync_to_async(self.search_manager.search_documents)(
            documents=data,
            context=context,
            keywords=keywords
        )

        return Response(results)

    # except Exception as e:
    #     print(f"[_handle_search] Error: {str(e)}")
    #     return Response(
    #         {'status': 'error', 'message': str(e)},
    #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #     )