from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def api_root(request):
    return Response({"message": "Welcome to the Django API DataStore"})


urlpatterns = [
    # path('', RedirectView.as_view(url='/api/', permanent=False)),
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/research/', include('research_assistant.urls')),
    path('api/auth/', include('auth_api.urls')),
]


