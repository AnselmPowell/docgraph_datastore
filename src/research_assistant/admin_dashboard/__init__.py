
from django.contrib import admin
from .dashboard import ResearchAssistantDashboard
from .ai_usage_dashboard import AIUsageDashboard  # Add this import

def initialize_dashboard():
    """Initialize the research assistant dashboard"""
    print("Initializing admin dashboards...")
    
    # Create the dashboards
    research_dashboard = ResearchAssistantDashboard(admin.site)
    ai_dashboard = AIUsageDashboard(admin.site)
    
    # Store references to the dashboards
    admin.site._research_dashboard = research_dashboard
    admin.site._ai_dashboard = ai_dashboard
    
    # Print available URLs for debugging
    print("Research dashboard URLs:", [url.name for url in research_dashboard.get_urls()])
    print("AI dashboard URLs:", [url.name for url in ai_dashboard.get_urls()])
    
    # Add dashboard URL patterns to admin site
    original_get_urls = admin.site.get_urls
    
    def get_urls():
        urls = original_get_urls()
        dashboard_urls = research_dashboard.get_urls() + ai_dashboard.get_urls()
        
        # Debug print all URLs
        print("All dashboard URLs:", [url.name for url in dashboard_urls])
        
        return dashboard_urls + urls
    
    # Only patch if not already patched
    if not hasattr(admin.site, '_research_dashboard'):
        admin.site.get_urls = get_urls
        print("Admin site URLs patched successfully")
    else:
        print("Admin site URLs already patched")