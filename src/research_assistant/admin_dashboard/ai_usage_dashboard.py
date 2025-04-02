from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta

from ..models import AIAPIUsage, SearchResult, DocumentMetadata

class AIUsageDashboard:
    """Admin dashboard for AI API usage metrics"""
    
    def __init__(self, admin_site):
        self.admin_site = admin_site
    
    def get_urls(self):
        """Add custom URLs for the dashboard"""
        return [
            path('ai-usage/', 
                self.admin_site.admin_view(self.dashboard_view),
                name='research_assistant_ai-usage'),  # Updated name format
            path('ai-usage/api/', 
                self.admin_site.admin_view(self.api_view),
                name='research_assistant_ai-usage-api'),  # Updated name format
        ]

    def dashboard_view(self, request):
        """Render the dashboard template"""
        context = {
            **self.admin_site.each_context(request),
            'title': 'AI API Usage Dashboard',
        }
        return TemplateResponse(
            request, 
            'research_assistant/ai_dashboard.html', 
            context
        )
    
    def api_view(self, request):
        """API endpoint to get AI usage dashboard data"""
        print("Starting AI API Usage data fetch")
        # Time periods for statistics
        now = timezone.now()
        one_month_ago = now - timedelta(days=30)
        one_week_ago = now - timedelta(days=7)
        
        # Get filter parameters
        user_id = request.GET.get('user_id')
        search_id = request.GET.get('search_id')
        model_name = request.GET.get('model_name')
        date_range = request.GET.get('date_range', '7')  # Default to 7 days
        
        print(f"Filters - user_id: {user_id}, search_id: {search_id}, model_name: {model_name}, date_range: {date_range}")
        
        # Base query
        usage_query = AIAPIUsage.objects.all()
        
        # Apply filters
        if user_id:
            usage_query = usage_query.filter(user_id=user_id)
        
        if search_id:
            usage_query = usage_query.filter(search_result_id=search_id)
            
        if model_name and model_name != 'all':
            usage_query = usage_query.filter(model_name=model_name)
            
        # Date range
        if date_range == '7':
            usage_query = usage_query.filter(created_at__gte=one_week_ago)
        elif date_range == '30':
            usage_query = usage_query.filter(created_at__gte=one_month_ago)
        
        # Get all users and searches for filter dropdowns
        all_users = list(User.objects.all().values('id', 'username', 'email'))
        all_searches = list(SearchResult.objects.all().values('id', 'query_context')[:100])
        all_models = list(AIAPIUsage.objects.values_list('model_name', flat=True).distinct())
        
        print(f"Found {len(all_users)} users, {len(all_searches)} searches, {len(all_models)} models")
        
        # Get overall metrics
        overall_metrics = usage_query.aggregate(
            total_cost=Sum('total_cost'),
            total_tokens=Sum('total_tokens'),
            total_calls=Count('id'),
            avg_duration=Sum(F('duration_ms')) / Count('id') if usage_query.exists() else 0
        )
        
        print(f"Overall metrics: {overall_metrics}")
        
        # Get metrics by search
        search_metrics = []
        if not search_id:  # Only if not filtering by specific search
            search_metrics = list(usage_query.filter(
                search_result__isnull=False
            ).values(
                'search_result_id', 
                'search_result__query_context'
            ).annotate(
                search_cost=Sum('total_cost'),
                search_tokens=Sum('total_tokens'),
                search_calls=Count('id')
            ).order_by('-search_cost')[:10])
        
        # Get metrics by user
        user_metrics = []
        if not user_id:  # Only if not filtering by specific user
            user_metrics = list(usage_query.filter(
                user__isnull=False
            ).values(
                'user_id', 
                'user__email'
            ).annotate(
                user_cost=Sum('total_cost'),
                user_tokens=Sum('total_tokens'),
                user_calls=Count('id')
            ).order_by('-user_cost')[:10])
        
        # Get metrics by model
        model_metrics = list(usage_query.values(
            'model_name'
        ).annotate(
            model_cost=Sum('total_cost'),
            model_tokens=Sum('total_tokens'),
            model_calls=Count('id')
        ).order_by('-model_cost'))
        
        print(f"Model metrics: {model_metrics}")
        
        # Get metrics by document
        document_metrics = []
        if not search_id:  # Only if not filtering by specific search
            document_metrics = list(usage_query.filter(
                document__isnull=False
            ).values(
                'document_id', 
                'document__title'
            ).annotate(
                doc_cost=Sum('total_cost'),
                doc_tokens=Sum('total_tokens'),
                doc_calls=Count('id')
            ).order_by('-doc_cost')[:10])
        
        # Get daily usage
        date_field = 'created_at__date'
        
        daily_usage = list(usage_query.values(date_field).annotate(
            date_cost=Sum('total_cost'),
            date_tokens=Sum('total_tokens'),
            date_calls=Count('id')
        ).order_by(date_field))
        
        # Format dates for JSON
        for item in daily_usage:
            if isinstance(item[date_field], timezone.datetime):
                item[date_field] = item[date_field].strftime('%Y-%m-%d')
            
        print(f"Daily usage: {len(daily_usage)} entries")
            
        # Get prompt and completion token breakdown
        token_breakdown = usage_query.aggregate(
            prompt_tokens=Sum('prompt_tokens'),
            completion_tokens=Sum('completion_tokens')
        )
        
        # Average cost per search
        avg_cost_per_search = 0
        if SearchResult.objects.count() > 0:
            total_cost = AIAPIUsage.objects.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
            avg_cost_per_search = total_cost / SearchResult.objects.count()
        
        print(f"Response data prepared, returning JSON")
        
        return JsonResponse({
            'overall_metrics': {
                'total_cost': float(overall_metrics['total_cost'] or 0),
                'total_tokens': overall_metrics['total_tokens'] or 0,
                'total_calls': overall_metrics['total_calls'] or 0,
                'avg_duration_ms': float(overall_metrics['avg_duration'] or 0),
            },
            'search_metrics': search_metrics,
            'user_metrics': user_metrics,
            'model_metrics': model_metrics,
            'document_metrics': document_metrics,
            'daily_usage': daily_usage,
            'token_breakdown': {
                'prompt_tokens': token_breakdown['prompt_tokens'] or 0,
                'completion_tokens': token_breakdown['completion_tokens'] or 0
            },
            'cost_metrics': {
                'avg_cost_per_search': float(avg_cost_per_search),
            },
            'filter_options': {
                'users': all_users,
                'searches': all_searches,
                'models': all_models
            }
        })