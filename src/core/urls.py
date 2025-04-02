from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from research_assistant.views.ai_dashboard import ai_dashboard_view, ai_dashboard_api

@api_view(['GET'])
def api_root(request):
    return Response({"message": "Welcome to the Django API DataStore"})

urlpatterns = [
    # path('', RedirectView.as_view(url='/api/', permanent=False)),
    path('', api_root, name='api-root'),

    path('api/research/', include('research_assistant.urls')),
    path('api/auth/', include('auth_api.urls')),
    
     # Dashboard URLs BEFORE admin.site.urls
    path('admin/ai-dashboard/', ai_dashboard_view, name='ai_dashboard'),
    path('admin/ai-dashboard/api/', ai_dashboard_api, name='ai_dashboard_api'),
    
    # Admin site URLs after the dashboard URLs
    path('admin/', admin.site.urls),
    
    path('api/research/', include('research_assistant.urls')),
    path('api/auth/', include('auth_api.urls')),
]