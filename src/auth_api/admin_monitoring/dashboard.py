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