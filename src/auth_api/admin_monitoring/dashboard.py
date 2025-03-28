# from django.contrib import admin
# from django.urls import path
# from django.http import JsonResponse
# from django.template.response import TemplateResponse
# from django.db.models import Count, Sum
# from django.utils import timezone
# from datetime import timedelta

# from ..models import UserProfile, UserSession, LoginAttempt


# class UserActivityDashboard:
#     """Admin dashboard for monitoring user activity"""
    
#     def __init__(self, admin_site):
#         self.admin_site = admin_site
    
#     def get_urls(self):
#         """Add custom URLs for the dashboard"""
#         urls = [
#             path('user-activity-dashboard/', 
#                  self.admin_site.admin_view(self.dashboard_view),
#                  name='user-activity-dashboard'),
#             path('user-activity-api/', 
#                  self.admin_site.admin_view(self.api_view),
#                  name='user-activity-api'),
#         ]
#         return urls

#     def dashboard_view(self, request):
#         """Render the dashboard template"""
#         context = {
#             **self.admin_site.each_context(request),
#             'title': 'User Activity Dashboard',
#         }
#         return TemplateResponse(request, 'admin/user_activity_dashboard.html', context)
    
#     def api_view(self, request):
#         """API endpoint to get dashboard data"""
#         # Time periods for statistics
#         now = timezone.now()
#         last_24h = now - timedelta(hours=24)
#         last_week = now - timedelta(days=7)
#         last_month = now - timedelta(days=30)
        
#         # User statistics
#         total_users = UserProfile.objects.count()
        
#         # Login method breakdown
#         login_methods = UserProfile.objects.values('is_social_account', 'social_provider') \
#             .annotate(count=Count('id'))
        
#         # Format login method data
#         auth_methods = {
#             'standard': UserProfile.objects.filter(is_social_account=False).count(),
#             'google': UserProfile.objects.filter(social_provider='google').count(),
#             'microsoft': UserProfile.objects.filter(social_provider='microsoft').count(),
#         }
        
#         # Recent activity
#         recent_logins = LoginAttempt.objects.filter(
#             was_successful=True,
#             attempt_time__gte=last_24h
#         ).count()
        
#         recent_failed_logins = LoginAttempt.objects.filter(
#             was_successful=False,
#             attempt_time__gte=last_24h
#         ).count()
        
#         active_sessions = UserSession.objects.filter(is_active=True).count()
        
#         # Time series data for login activity
#         daily_logins = LoginAttempt.objects.filter(
#             was_successful=True,
#             attempt_time__gte=last_week
#         ).values('attempt_time__date') \
#          .annotate(count=Count('id')) \
#          .order_by('attempt_time__date')
        
#         return JsonResponse({
#             'user_stats': {
#                 'total_users': total_users,
#                 'auth_methods': auth_methods,
#             },
#             'activity': {
#                 'recent_logins': recent_logins,
#                 'recent_failed_logins': recent_failed_logins,
#                 'active_sessions': active_sessions,
#             },
#             'time_series': {
#                 'daily_logins': list(daily_logins),
#             }
#         })


# def initialize_dashboard(admin_site):
#     """Initialize and attach dashboard to admin site"""
#     dashboard = UserActivityDashboard(admin_site)
#     admin_site.register_view = getattr(admin_site, 'register_view', lambda *args: None)
#     admin_site.register_view('user-activity-dashboard', dashboard.dashboard_view)
    
#     # Add dashboard URLs to admin site
#     admin_site._registry_views = getattr(admin_site, '_registry_views', {})
#     admin_site._registry_views['user-activity-dashboard'] = dashboard
    
#     # Patch get_urls to include dashboard URLs
#     original_get_urls = admin_site.get_urls
    
#     def get_urls():
#         urls = original_get_urls()
#         if hasattr(dashboard, 'get_urls'):
#             urls += dashboard.get_urls()
#         return urls
    
#     admin_site.get_urls = get_urls





from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

from ..models import UserProfile, UserSession, LoginAttempt


class UserActivityDashboard:
    """Admin dashboard for monitoring user activity"""
    
    def __init__(self, admin_site):
        self.admin_site = admin_site
    
    def get_urls(self):
        """Add custom URLs for the dashboard"""
        return [
            path('user-activity/', self.dashboard_view, name='user-activity-dashboard'),
            path('user-activity/api/', self.api_view, name='user-activity-api'),
        ]

    def dashboard_view(self, request):
        """Render the dashboard template"""
        context = {
            **self.admin_site.each_context(request),
            'title': 'User Activity Dashboard',
        }
        return TemplateResponse(request, 'admin/user_activity_dashboard.html', context)
    
    def api_view(self, request):
        """API endpoint to get dashboard data"""
        # Time periods for statistics
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_week = now - timedelta(days=7)
        
        # User statistics
        total_users = UserProfile.objects.count()
        
        # Login method breakdown
        auth_methods = {
            'standard': UserProfile.objects.filter(is_social_account=False).count(),
            'google': UserProfile.objects.filter(social_provider='google').count(),
            'microsoft': UserProfile.objects.filter(social_provider='microsoft').count(),
        }
        
        # Recent activity
        recent_logins = LoginAttempt.objects.filter(
            was_successful=True,
            attempt_time__gte=last_24h
        ).count()
        
        recent_failed_logins = LoginAttempt.objects.filter(
            was_successful=False,
            attempt_time__gte=last_24h
        ).count()
        
        active_sessions = UserSession.objects.filter(is_active=True).count()
        
        # Time series data for login activity
        daily_logins = list(LoginAttempt.objects.filter(
            was_successful=True,
            attempt_time__gte=last_week
        ).values('attempt_time__date') \
         .annotate(count=Count('id')) \
         .order_by('attempt_time__date').values('attempt_time__date', 'count'))
        
        # Convert datetime to string for JSON serialization
        for item in daily_logins:
            if isinstance(item['attempt_time__date'], timezone.datetime):
                item['attempt_time__date'] = item['attempt_time__date'].strftime('%Y-%m-%d')
        
        return JsonResponse({
            'user_stats': {
                'total_users': total_users,
                'auth_methods': auth_methods,
            },
            'activity': {
                'recent_logins': recent_logins,
                'recent_failed_logins': recent_failed_logins,
                'active_sessions': active_sessions,
            },
            'time_series': {
                'daily_logins': daily_logins,
            }
        })