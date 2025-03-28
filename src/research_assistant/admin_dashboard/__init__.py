from django.contrib import admin
from .dashboard import ResearchAssistantDashboard

def initialize_dashboard():
    """Initialize the research assistant dashboard"""
    # Create the dashboard
    dashboard = ResearchAssistantDashboard(admin.site)
    
    # Store reference to the dashboard
    admin.site._research_dashboard = dashboard
    
    # Add dashboard URL patterns to admin site
    original_get_urls = admin.site.get_urls
    
    def get_urls():
        urls = original_get_urls()
        dashboard_urls = dashboard.get_urls()
        return dashboard_urls + urls
    
    # Only patch if not already patched
    if not hasattr(admin.site, '_research_dashboard'):
        admin.site.get_urls = get_urls