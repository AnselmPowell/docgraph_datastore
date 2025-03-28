# from django.apps import AppConfig


# class AuthConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'auth_api'

#     def ready(self):
#         # Import and initialize admin monitoring
#         from .admin_monitoring import setup_admin_monitoring
#         setup_admin_monitoring()




from django.apps import AppConfig

class AuthApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_api'
    verbose_name = 'Authentication & User Management'
    
    def ready(self):
        # Import and initialize admin monitoring
        try:
            from .admin_monitoring import setup_admin_monitoring
            setup_admin_monitoring()
        except ImportError:
            # Handle error gracefully for initial migrations
            print("Note: Admin monitoring not fully set up yet. Will be available after migrations.")