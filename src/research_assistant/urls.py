from django.urls import path
from .views import ResearchAnalysisViewSet

urlpatterns = [
    path(
        'analyze_documents/',
        ResearchAnalysisViewSet.as_view({'post': 'analyze_documents'}),
        name='analyze-documents'
    ),
]