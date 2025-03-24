# src/research_assistant/views/arxiv_search.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from ..services.arxiv_searcher import ArxivSearcher
from ..services.search_term_generator import SearchTermGenerator
from ..models import ResearchContext

@method_decorator(csrf_exempt, name='dispatch')
class ArxivSearchViewSet(viewsets.ViewSet):
    """Handle arXiv search requests"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.arxiv_searcher = ArxivSearcher()
        self.search_term_generator = SearchTermGenerator()
    
    @action(detail=False, methods=['POST'])
    def direct_search(self, request):
        """Handle direct search requests"""
        print("DIRECT SEARCH---")
        query = request.data.get('query')
        max_results = request.data.get('max_results', 5)
        
        if not query:
            return Response({
                'status': 'error',
                'message': 'No search query provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Search arXiv
            results = self.arxiv_searcher.search(query, max_results=max_results)
            print("complete results", results)

            return Response({
                'status': 'success',
                'results': results,
                'query': query
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['POST'])
    def context_search(self, request):
        print("CONTEXT SEARCH----")
        """Handle context-based search requests"""
        context_id = request.data.get('context_id')
        max_results_per_term = request.data.get('max_results_per_term', 3)
        
        if not context_id:
            return Response({
                'status': 'error',
                'message': 'No context ID provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the research context
            try:
                context = ResearchContext.objects.get(id=context_id, user=request.user)
            except ResearchContext.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Research context not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Generate search terms from context
            print("Generate search terms ......")
            search_terms_data = self.search_term_generator.generate_search_terms(context.content)
            print(" search terms data.:", search_terms_data)
            # Search arXiv for each search term
            categories_results = []
            
            for category in search_terms_data['categories']:
                category_results = {
                    'category': category['category'],
                    'description': category['description'],
                    'search_terms': category['search_terms'],
                    'papers': []
                }
                
                # Search for each term in the category
                for term in category['search_terms']:
                    papers = self.arxiv_searcher.search(term, max_results=max_results_per_term)
                    # print("search results:", papers)
                    
                    # Add search term to each paper result
                    for paper in papers:
                        paper['search_term'] = term
                    
                    category_results['papers'].extend(papers)
                
                categories_results.append(category_results)
            
            return Response({
                'status': 'success',
                'categories': categories_results,
                'context_id': str(context.id),
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)