# from django.contrib import admin
# from .dashboard import initialize_dashboard

# # Initialize admin monitoring components
# def setup_admin_monitoring():
#     initialize_dashboard(admin.site)



from django.contrib import admin
from .dashboard import UserActivityDashboard

# Initialize admin monitoring components
def setup_admin_monitoring():
    """Set up the admin dashboard"""
    # Only modify the admin site if it hasn't been modified already
    if not hasattr(admin.site, 'user_activity_dashboard'):
        # Create the dashboard
        dashboard = UserActivityDashboard(admin.site)
        admin.site.user_activity_dashboard = dashboard
        
        # Add dashboard URL patterns to admin site
        original_get_urls = admin.site.get_urls
        
        def get_urls():
            urls = original_get_urls()
            dashboard_urls = dashboard.get_urls()
            # Make sure these URLs are properly namespaced to avoid conflicts
            for url in dashboard_urls:
                url.name = f'admin:{url.name}'
            return dashboard_urls + urls
        
        admin.site.get_urls = get_urls