
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
import threading
import uuid
from threading import Lock

from ..models import SearchResult, DocumentMetadata
from ..services.search.search_manager import SearchManager

@method_decorator(csrf_exempt, name='dispatch')
class DocumentSearchViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_manager = SearchManager()
        self.search_threads = {}
        self.thread_lock = Lock()
        self.max_concurrent_searches = 3  # Limit concurrent search operations
        print("[DocumentSearchViewSet] Initialized")

    # @action(detail=False, methods=['POST'])
    # def search_results(self, request):
    #     """Create a search with background processing"""
    #     print(f"[search_results] Starting search for user: {request.user.email}")
        
    #     data = request.data
    #     context = data.get('context')
    #     keywords = data.get('keywords', [])
    #     file_names = data.get('file_name')
        
    #     print("Does it have context")
       
    #     if not context or not file_names:
    #         return Response({
    #             'status': 'error',
    #             'message': 'Missing required fields',
    #             'detail': 'Both context and file_name are required'
    #         }, status=status.HTTP_400_BAD_REQUEST)
        
    #     print("Context: ", context)
        
    #     # Immediately create pending search results
    #     pending_results = []
        
    #     try:
    #         for file_name in file_names:
    #             print("get document ", file_name)
    #             # Get document
    #             document = DocumentMetadata.objects.filter(
    #                 title=file_name,
    #                 user=request.user,
    #             ).first()
                
    #             if not document:
    #                 print("document not found")
    #                 continue
                
    #             print("document found", document)
    #             # Create pending search result
    #             search_id = uuid.uuid4()
    #             search_result = SearchResult.objects.create(
    #                 id=search_id,
    #                 user=request.user,
    #                 document=document,
    #                 query_context=context,
    #                 keywords=keywords,
    #                 document_title=document.title or document.file_name,
    #                 document_authors=document.authors or [],
    #                 document_summary=document.summary,
    #                 relevance_score=0,  # Will be updated
    #                 matching_sections=[],  # Will be updated
    #                 processing_status='pending'
    #             )
                
    #             pending_result = {
    #                 'search_results_id': str(search_id),
    #                 'document_id': str(document.id),
    #                 'title': document.title or document.file_name,
    #                 'question': context,
    #                 'keywords': keywords,
    #                 'authors': document.authors or [],
    #                 'summary': document.summary,
    #                 'relevance_score': 0,
    #                 'matching_sections': [],
    #                 'processing_status': 'pending'
    #             }
                
    #             pending_results.append(pending_result)
                
    #             # Start background processing
    #             with self.thread_lock:
    #                 if len(self.search_threads) < self.max_concurrent_searches:
    #                     thread = threading.Thread(
    #                         target=self._process_search_background,
    #                         args=(search_id, document, context, keywords, request.user)
    #                     )
    #                     thread.daemon = True
    #                     self.search_threads[str(search_id)] = thread
    #                     thread.start()
    #                 else:
    #                     # Mark for later processing
    #                     print(f"[search_results] Search {search_id} queued for later processing")
            
    #         return Response({
    #             'status': 'success',
    #             'results': pending_results,
    #             'total_matches': len(pending_results)
    #         })
            
    #     except Exception as e:
    #         print(f"[search_results] Error creating search: {str(e)}")
    #         return Response({
    #             'status': 'error',
    #             'message': 'Search creation failed',
    #             'detail': str(e)
    #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def search_results(self, request):
        """Create a search with background processing"""
        print(f"[search_results] Starting search for user: {request.user.email}")
        
        data = request.data
        context = data.get('context')
        keywords = data.get('keywords', [])
        file_names = data.get('file_name')
        
        print("Does it have context")
    
        if not context or not file_names:
            return Response({
                'status': 'error',
                'message': 'Missing required fields',
                'detail': 'Both context and file_name are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print("Context: ", context)
        
        # Immediately create pending search results
        pending_results = []
        
        try:
            for file_name in file_names:
                print("get document ", file_name)
                # Get document
                document = DocumentMetadata.objects.filter(
                    title=file_name,
                    user=request.user,
                ).first()
                
                if not document:
                    print("document not found")
                    continue
                
                print("document found", document)
                # Create pending search result
                search_id = uuid.uuid4()
                search_result = SearchResult.objects.create(
                    id=search_id,
                    user=request.user,
                    document=document,
                    query_context=context,
                    keywords=keywords,
                    document_title=document.title or document.file_name,
                    document_authors=document.authors or [],
                    document_summary=document.summary,
                    relevance_score=0,  # Will be updated
                    matching_sections=[],  # Will be updated
                    processing_status='pending'
                )
                
                pending_result = {
                    'search_results_id': str(search_id),
                    'document_id': str(document.id),
                    'title': document.title or document.file_name,
                    'question': context,
                    'keywords': keywords,
                    'authors': document.authors or [],
                    'summary': document.summary,
                    'relevance_score': 0,
                    'matching_sections': [],
                    'processing_status': 'pending'
                }
                
                pending_results.append(pending_result)
                
                # Start background processing
                with self.thread_lock:
                    if len(self.search_threads) < self.max_concurrent_searches:
                        thread = threading.Thread(
                            target=self._process_search_background,
                            args=(search_id, document, context, keywords, request.user)
                        )
                        thread.daemon = True
                        self.search_threads[str(search_id)] = thread
                        thread.start()
                    else:
                        # Mark for later processing
                        print(f"[search_results] Search {search_id} queued for later processing")
            
            return Response({
                'status': 'success',
                'results': pending_results,
                'total_matches': len(pending_results)
            })
            
        except Exception as e:
            print(f"[search_results] Error creating search: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Search creation failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # def _process_search_background(self, search_id, document, context, keywords, user):
    #     """Process search in background thread"""
    #     search_id_str = str(search_id)
    #     try:
    #         print(f"[_process_search_background] Processing search {search_id} for document: {document.file_name}")
            
    #         # Update status to processing
    #         search_result = SearchResult.objects.get(id=search_id)
    #         search_result.processing_status = 'processing'
    #         search_result.save()
            
    #         # Prepare search data
    #         search_data = [{
    #             'file_name': document.file_name,
    #             'context': context,
    #             'keywords': keywords,
    #             'user': user
    #         }]
            
    #         # Perform search
    #         results = self.search_manager.search_documents(
    #             search_data=search_data,
    #             context=context,
    #             keywords=keywords,
    #             user=user
    #         )
            
    #         # Get the result for this document
    #         for result in results.get('results', []):
    #             if str(result['document_id']) == str(document.id):
    #                 # Update search result with actual data
    #                 search_result.matching_sections = result['matching_sections']
    #                 search_result.relevance_score = result['relevance_score']
    #                 search_result.processing_status = 'completed'
    #                 search_result.save()
    #                 break
            
    #         print(f"[_process_search_background] Completed search {search_id}")
            
    #     except Exception as e:
    #         print(f"[_process_search_background] Error processing search {search_id}: {str(e)}")
            
    #         try:
    #             # Update status to failed
    #             search_result = SearchResult.objects.get(id=search_id)
    #             search_result.processing_status = 'failed'
    #             search_result.error_message = str(e)
    #             search_result.save()
    #         except Exception as inner_e:
    #             print(f"[_process_search_background] Failed to update search status: {str(inner_e)}")
                
    #     finally:
    #         # Remove thread from tracking with thread safety
    #         with self.thread_lock:
    #             if search_id_str in self.search_threads:
    #                 del self.search_threads[search_id_str]
    #                 print(f"[_process_search_background] Removed thread for search {search_id_str}")
            
    #         # Start next pending search after removing the current thread
    #         # Call outside the lock to avoid deadlocks
    #         self._process_next_pending_search(user)
    #         print(f"[_process_search_background] Checked for next pending search")
    
    # def _process_next_pending_search(self, user):
    #     """Process the next pending search if we have capacity"""
    #     print(f"[_process_next_pending_search] Current thread count: {len(self.search_threads)}")
        
    #     with self.thread_lock:
    #         # Skip if at capacity
    #         if len(self.search_threads) >= self.max_concurrent_searches:
    #             print(f"[_process_next_pending_search] At capacity ({self.max_concurrent_searches}), not starting new searches")
    #             return
                    
    #         # Find pending searches - get ALL pending searches first
    #         pending_searches = SearchResult.objects.filter(
    #             processing_status='pending'
    #         ).order_by('created_at')[:5]  # Limit query size but get multiple
            
    #         print(f"[_process_next_pending_search] Found {pending_searches.count()} pending searches")
            
    #         # Try to start as many searches as we have capacity for
    #         started = 0
    #         for pending_search in pending_searches:
    #             # Skip if we reached capacity during this loop
    #             if len(self.search_threads) >= self.max_concurrent_searches:
    #                 print(f"[_process_next_pending_search] Reached capacity during processing")
    #                 break
                    
    #             search_id = pending_search.id
    #             document = pending_search.document
    #             context = pending_search.query_context
    #             keywords = pending_search.keywords
    #             search_user = pending_search.user
                
    #             # Skip if already being processed
    #             if str(search_id) in self.search_threads:
    #                 print(f"[_process_next_pending_search] Search {search_id} already being processed")
    #                 continue
                    
    #             # Start thread
    #             thread = threading.Thread(
    #                 target=self._process_search_background,
    #                 args=(search_id, document, context, keywords, search_user)
    #             )
    #             thread.daemon = True
    #             self.search_threads[str(search_id)] = thread
    #             thread.start()
    #             started += 1
    #             print(f"[_process_next_pending_search] Started processing search {search_id}")
                
    #         print(f"[_process_next_pending_search] Started {started} new searches")

    def _process_search_background(self, search_id, document, context, keywords, user):
        """Process search in background thread"""
        search_id_str = str(search_id)
        try:
            print(f"[_process_search_background] Processing search {search_id} for document: {document.file_name}")
            
            # Update status to processing
            search_result = SearchResult.objects.get(id=search_id)
            search_result.processing_status = 'processing'
            search_result.save()
            
            # Prepare search data
            search_data = [{
                'file_name': document.file_name,
                'context': context,
                'keywords': keywords,
                'user': user
            }]
            
            # Perform search
            results = self.search_manager.search_documents(
                search_data=search_data,
                context=context,
                keywords=keywords,
                user=user
            )
            
            # Store API usage data
            if 'api_usage' in results:
                usage_data = results['api_usage']
                
                # Create aggregated record
                from ..models import AIAPIUsage
                from decimal import Decimal
                
                aggregated_usage = AIAPIUsage.objects.create(
                    user=user,
                    search_result=search_result,
                    document=document,
                    model_name="multiple",  # Will be a mix of models
                    prompt=context[:1000],  # Store a truncated version of prompt
                    prompt_tokens=sum(usage['prompt_tokens'] for usage in usage_data['details']),
                    completion_tokens=sum(usage['completion_tokens'] for usage in usage_data['details']),
                    total_tokens=usage_data['tokens'],
                    total_cost=Decimal(str(usage_data['cost'])),
                    is_aggregated=True,
                    api_calls_count=usage_data['calls'],
                    start_time=min(usage['start_time'] for usage in usage_data['details'] if 'start_time' in usage),
                    end_time=max(usage['end_time'] for usage in usage_data['details'] if 'end_time' in usage)
                )
                
                # Now store detailed usage records for each API call
                for usage in usage_data['details']:
                    try:
                        AIAPIUsage.objects.create(
                            user=user,
                            search_result=search_result,
                            document=DocumentMetadata.objects.get(id=usage['document_id']) if 'document_id' in usage else None,
                            model_name=usage['model_name'],
                            prompt=usage['prompt'][:1000],  # Truncate prompt
                            prompt_tokens=usage['prompt_tokens'],
                            completion_tokens=usage['completion_tokens'],
                            total_tokens=usage['total_tokens'],
                            cost_per_1k_prompt_tokens=Decimal(str(usage['cost_per_1k_prompt_tokens'])),
                            cost_per_1k_completion_tokens=Decimal(str(usage['cost_per_1k_completion_tokens'])),
                            total_cost=Decimal(str(usage['total_cost'])),
                            start_time=usage['start_time'],
                            end_time=usage['end_time'],
                            duration_ms=usage['duration_ms'],
                            is_aggregated=False
                        )
                    except Exception as e:
                        print(f"Error storing API usage record: {str(e)}")
            
            # Get the result for this document
            for result in results.get('results', []):
                if str(result['document_id']) == str(document.id):
                    # Update search result with actual data
                    search_result.matching_sections = result['matching_sections']
                    search_result.relevance_score = result['relevance_score']
                    search_result.processing_status = 'completed'
                    search_result.save()
                    break
            
            print(f"[_process_search_background] Completed search {search_id}")
            
        except Exception as e:
            print(f"[_process_search_background] Error processing search {search_id}: {str(e)}")
            
            try:
                # Update status to failed
                search_result = SearchResult.objects.get(id=search_id)
                search_result.processing_status = 'failed'
                search_result.error_message = str(e)
                search_result.save()
            except Exception as inner_e:
                print(f"[_process_search_background] Failed to update search status: {str(inner_e)}")
                
        finally:
            # Remove thread from tracking with thread safety
            with self.thread_lock:
                if search_id_str in self.search_threads:
                    del self.search_threads[search_id_str]
                    print(f"[_process_search_background] Removed thread for search {search_id_str}")
            
            # Start next pending search after removing the current thread
            # Call outside the lock to avoid deadlocks
            self._process_next_pending_search(user)
            print(f"[_process_search_background] Checked for next pending search")

    def _process_next_pending_search(self, user):
        """Process the next pending search if we have capacity"""
        print(f"[_process_next_pending_search] Current thread count: {len(self.search_threads)}")
        
        with self.thread_lock:
            # Skip if at capacity
            if len(self.search_threads) >= self.max_concurrent_searches:
                print(f"[_process_next_pending_search] At capacity ({self.max_concurrent_searches}), not starting new searches")
                return
                    
            # Find pending searches - get ALL pending searches first
            pending_searches = SearchResult.objects.filter(
                processing_status='pending'
            ).order_by('created_at')[:5]  # Limit query size but get multiple
            
            print(f"[_process_next_pending_search] Found {pending_searches.count()} pending searches")
            
            # Try to start as many searches as we have capacity for
            started = 0
            for pending_search in pending_searches:
                # Skip if we reached capacity during this loop
                if len(self.search_threads) >= self.max_concurrent_searches:
                    print(f"[_process_next_pending_search] Reached capacity during processing")
                    break
                    
                search_id = pending_search.id
                document = pending_search.document
                context = pending_search.query_context
                keywords = pending_search.keywords
                search_user = pending_search.user
                
                # Skip if already being processed
                if str(search_id) in self.search_threads:
                    print(f"[_process_next_pending_search] Search {search_id} already being processed")
                    continue
                    
                # Start thread
                thread = threading.Thread(
                    target=self._process_search_background,
                    args=(search_id, document, context, keywords, search_user)
                )
                thread.daemon = True
                self.search_threads[str(search_id)] = thread
                thread.start()
                started += 1
                print(f"[_process_next_pending_search] Started processing search {search_id}")
                
            print(f"[_process_next_pending_search] Started {started} new searches")

    @action(detail=False, methods=['POST'], url_path='check-status')
    def check_search_status(self, request):
        """Check status of search results"""
        search_ids = request.data.get('search_ids', [])
        
        if not search_ids:
            return Response({
                'status': 'error',
                'message': 'No search IDs provided'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Query search results with provided IDs
            search_results = SearchResult.objects.filter(
                id__in=search_ids,
                user=request.user
            )
            
            formatted_results = []
            for result in search_results:
                formatted_result = {
                    'search_results_id': str(result.id),
                    'document_id': str(result.document.id),
                    'title': result.document_title,
                    'question': result.query_context,
                    'keywords': result.keywords,
                    'authors': result.document_authors,
                    'summary': result.document_summary,
                    'relevance_score': result.relevance_score,
                    'matching_sections': result.matching_sections,
                    'processing_status': result.processing_status,
                    'error_message': result.error_message
                }
                formatted_results.append(formatted_result)
                
            return Response({
                'status': 'success',
                'results': formatted_results
            })
            
        except Exception as e:
            print(f"[check_search_status] Error: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                    'search_results_id': str(result.id),
                    'document_id': str(result.document.id),
                    'title': result.document_title,
                    'question': result.query_context,
                    'keywords': result.keywords,
                    'authors': result.document_authors,
                    'summary': result.document_summary,
                    'relevance_score': result.relevance_score,
                    'matching_sections': result.matching_sections,
                    'processing_status': result.processing_status,
                    'error_message': result.error_message
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
            
            # Cancel any ongoing processing
            with self.thread_lock:
                if str(search_result_id) in self.search_threads:
                    # We can't actually kill the thread, but we'll remove it from tracking
                    del self.search_threads[str(search_result_id)]

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