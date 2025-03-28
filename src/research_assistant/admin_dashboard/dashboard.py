# from django.contrib import admin
# from django.urls import path
# from django.http import JsonResponse
# from django.template.response import TemplateResponse
# from django.db.models import Count, Q, F
# from django.contrib.auth.models import User
# from django.utils import timezone
# from datetime import timedelta

# from ..models import DocumentMetadata, SearchResult
# from auth_api.models import LoginAttempt, UserSession, UserProfile


# class ResearchAssistantDashboard:
#     """Admin dashboard for Research Assistant metrics"""
    
#     def __init__(self, admin_site):
#         self.admin_site = admin_site
    
#     def get_urls(self):
#         """Add custom URLs for the dashboard"""
#         return [
#             path('research-metrics/', 
#                 self.admin_site.admin_view(self.dashboard_view),
#                 name='research-metrics-dashboard'),
#             path('research-metrics/api/', 
#                 self.admin_site.admin_view(self.api_view),
#                 name='research-metrics-api'),
#         ]

#     def dashboard_view(self, request):
#         """Render the dashboard template"""
#         context = {
#             **self.admin_site.each_context(request),
#             'title': 'Research Assistant Metrics',
#         }
#         return TemplateResponse(
#             request, 
#             'admin/research_assistant/dashboard.html', 
#             context
#         )
    
#     def api_view(self, request):
#         """API endpoint to get dashboard data"""
#         # Time periods for statistics
#         now = timezone.now()
#         one_month_ago = now - timedelta(days=30)
#         two_months_ago = now - timedelta(days=60)
#         one_week_ago = now - timedelta(days=7)
#         two_weeks_ago = now - timedelta(days=14)
        
#         # 1. Total Registered Users
#         total_users = User.objects.count()
        
#         # 2. Active Users (uploaded at least one document AND searched)
#         document_uploaders = User.objects.filter(
#             documents__isnull=False
#         ).distinct().values_list('id', flat=True)
        
#         searchers = User.objects.filter(
#             search_results__isnull=False
#         ).distinct().values_list('id', flat=True)
        
#         active_users_count = User.objects.filter(
#             id__in=document_uploaders
#         ).filter(
#             id__in=searchers
#         ).count()
        
#         # 3. Returning users after a month
#         # Find users who were active 1-2 months ago AND in the last month
#         users_active_previous_month = set(LoginAttempt.objects.filter(
#             was_successful=True,
#             attempt_time__gte=two_months_ago,
#             attempt_time__lt=one_month_ago
#         ).values_list('email', flat=True).distinct())
        
#         users_returned_this_month = set(LoginAttempt.objects.filter(
#             was_successful=True,
#             attempt_time__gte=one_month_ago
#         ).values_list('email', flat=True).distinct())
        
#         returning_monthly_users = len(users_active_previous_month.intersection(users_returned_this_month))
        
#         # 4. Weekly users
#         # Find users who logged in at least once in the last 7 days
#         weekly_users = LoginAttempt.objects.filter(
#             was_successful=True,
#             attempt_time__gte=one_week_ago
#         ).values('email').distinct().count()
        
#         # 5. Users returning every 1-2 days
#         # This is complex - we need to analyze login patterns
#         # For simplicity, we'll approximate by counting users with >3 logins in the last week
#         frequent_users = LoginAttempt.objects.filter(
#             was_successful=True,
#             attempt_time__gte=one_week_ago
#         ).values('email').annotate(
#             login_count=Count('id')
#         ).filter(login_count__gte=3).count()
        
#         # Get user engagement trend data
#         user_trend_data = []
#         for i in range(30):
#             day = now - timedelta(days=i)
#             day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
#             day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
#             logins = LoginAttempt.objects.filter(
#                 was_successful=True,
#                 attempt_time__gte=day_start,
#                 attempt_time__lte=day_end
#             ).values('email').distinct().count()
            
#             documents = DocumentMetadata.objects.filter(
#                 created_at__gte=day_start,
#                 created_at__lte=day_end
#             ).count()
            
#             searches = SearchResult.objects.filter(
#                 created_at__gte=day_start,
#                 created_at__lte=day_end
#             ).count()
            
#             user_trend_data.append({
#                 'date': day_start.strftime('%Y-%m-%d'),
#                 'logins': logins,
#                 'documents': documents,
#                 'searches': searches
#             })
        
#         return JsonResponse({
#             'user_metrics': {
#                 'total_users': total_users,
#                 'active_users': active_users_count,
#                 'returning_monthly_users': returning_monthly_users,
#                 'weekly_users': weekly_users,
#                 'frequent_users': frequent_users,
#             },
#             'engagement_trends': user_trend_data
#         })


from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.db.models import Count, Q, F
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from ..models import DocumentMetadata, SearchResult
from auth_api.models import LoginAttempt, UserSession, UserProfile


class ResearchAssistantDashboard:
    """Admin dashboard for Research Assistant metrics"""
    
    def __init__(self, admin_site):
        self.admin_site = admin_site
    
    def get_urls(self):
        """Add custom URLs for the dashboard"""
        return [
            path('research-metrics/', 
                self.admin_site.admin_view(self.dashboard_view),
                name='research-metrics-dashboard'),
            path('research-metrics/api/', 
                self.admin_site.admin_view(self.api_view),
                name='research-metrics-api'),
        ]



    def dashboard_view(self, request):
        """Render the dashboard template"""
        context = {
            **self.admin_site.each_context(request),
            'title': 'Research Assistant Metrics',
        }
        return TemplateResponse(
            request, 
            'admin/research_assistant/dashboard.html', 
            context
        )
    
    def api_view(self, request):
        """API endpoint to get dashboard data"""
        # Time periods for statistics
        now = timezone.now()
        one_month_ago = now - timedelta(days=30)
        two_months_ago = now - timedelta(days=60)
        one_week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        # Get filter parameters
        user_id = request.GET.get('user_id')
        query_id = request.GET.get('query_id')
        
        # Initialize basic data
        all_users = list(User.objects.filter(is_staff=False).values('id', 'username', 'email'))
        all_queries = list(SearchResult.objects.values('query_context').annotate(
            count=Count('id')).order_by('-count')[:100])
        
        # Apply user filter to base querysets if specified
        user_filter = {}
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                user_filter = {'user': user}
            except User.DoesNotExist:
                pass
        
        # 1. Total Registered Users (never filtered)
        total_users = User.objects.filter(is_staff=False).count()
        
        # 2. Active Users (uploaded at least one document AND searched)
        document_uploaders_query = User.objects.filter(documents__isnull=False)
        searchers_query = User.objects.filter(search_results__isnull=False)
        
        # Apply user filter if specified
        if user_id:
            document_uploaders = [int(user_id)] if DocumentMetadata.objects.filter(user_id=user_id).exists() else []
            searchers = [int(user_id)] if SearchResult.objects.filter(user_id=user_id).exists() else []
        else:
            document_uploaders = document_uploaders_query.distinct().values_list('id', flat=True)
            searchers = searchers_query.distinct().values_list('id', flat=True)
        
        active_users_count = len(set(document_uploaders).intersection(set(searchers)))
        
        # 3. Returning users after a month
        login_attempts_base = LoginAttempt.objects.filter(was_successful=True)
        
        # Apply email filter if user_id specified
        if user_id:
            try:
                user_email = User.objects.get(id=user_id).email
                login_attempts_base = login_attempts_base.filter(email=user_email)
            except User.DoesNotExist:
                pass
        
        users_active_previous_month = set(login_attempts_base.filter(
            attempt_time__gte=two_months_ago,
            attempt_time__lt=one_month_ago
        ).values_list('email', flat=True).distinct())
        
        users_returned_this_month = set(login_attempts_base.filter(
            attempt_time__gte=one_month_ago
        ).values_list('email', flat=True).distinct())
        
        returning_monthly_users = len(users_active_previous_month.intersection(users_returned_this_month))
        
        # 4. Weekly users
        weekly_users_query = login_attempts_base.filter(
            attempt_time__gte=one_week_ago
        )
        weekly_users = weekly_users_query.values('email').distinct().count()
        
        # 5. Users returning every 1-2 days
        frequent_users_query = login_attempts_base.filter(
            attempt_time__gte=one_week_ago
        ).values('email').annotate(
            login_count=Count('id')
        ).filter(login_count__gte=3)
        frequent_users = frequent_users_query.count()
        
        # Get user engagement trend data
        user_trend_data = []
        
        documents_base = DocumentMetadata.objects
        searches_base = SearchResult.objects
        
        # Apply user filter to document and search queries
        if user_id:
            documents_base = documents_base.filter(user_id=user_id)
            searches_base = searches_base.filter(user_id=user_id)
        
        # Apply query filter to search results if specified
        if query_id:
            searches_base = searches_base.filter(query_context=query_id)
        
        for i in range(30):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Apply login filter for trends
            login_filter = {'was_successful': True, 
                           'attempt_time__gte': day_start,
                           'attempt_time__lte': day_end}
            
            if user_id:
                try:
                    user_email = User.objects.get(id=user_id).email
                    login_filter['email'] = user_email
                except User.DoesNotExist:
                    pass
            
            logins = LoginAttempt.objects.filter(
                **login_filter
            ).values('email').distinct().count()
            
            documents = documents_base.filter(
                created_at__gte=day_start,
                created_at__lte=day_end
            ).count()
            
            searches = searches_base.filter(
                created_at__gte=day_start,
                created_at__lte=day_end
            ).count()
            
            user_trend_data.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'logins': logins,
                'documents': documents,
                'searches': searches
            })
        
        # Get search result data if query specified
        search_results_data = []
        if query_id:
            search_results_query = SearchResult.objects.filter(query_context=query_id)
            
            if user_id:
                search_results_query = search_results_query.filter(user_id=user_id)
                
            search_results_data = list(search_results_query.values(
                'id', 'document_title', 'relevance_score', 'processing_status', 'created_at'
            ).order_by('-relevance_score')[:50])
            
            # Format datetime objects for JSON serialization
            for result in search_results_data:
                result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Get user documents if user_id specified
        user_documents = []
        if user_id:
            user_documents = list(DocumentMetadata.objects.filter(
                user_id=user_id
            ).values('id', 'title', 'file_name', 'processing_status', 'created_at')[:50])
            
            # Format datetime objects for JSON serialization
            for doc in user_documents:
                doc['created_at'] = doc['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return JsonResponse({
            'user_metrics': {
                'total_users': total_users,
                'active_users': active_users_count,
                'returning_monthly_users': returning_monthly_users,
                'weekly_users': weekly_users,
                'frequent_users': frequent_users,
            },
            'engagement_trends': user_trend_data,
            'filter_options': {
                'users': all_users,
                'queries': all_queries
            },
            'filter_results': {
                'search_results': search_results_data,
                'user_documents': user_documents
            },
            'active_filters': {
                'user_id': user_id,
                'query_id': query_id
            }
        })