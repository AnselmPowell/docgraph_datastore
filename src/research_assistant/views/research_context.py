# in research_assistant/views/research_context.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from ..models import ResearchContext

class ResearchContextViewSet(viewsets.ViewSet):
    """Handle research context operations"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get user's research context"""
        try:
            context = ResearchContext.objects.filter(user=request.user).first()
            
            if not context:
                return Response({
                    'status': 'success',
                    'has_context': False,
                    'message': 'No research context found'
                })
            
            return Response({
                'status': 'success',
                'has_context': True,
                'context': {
                    'id': str(context.id),
                    'content': context.content,
                    'created_at': context.created_at,
                    'updated_at': context.updated_at
                }
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request):
        """Create or update research context"""
        try:
            data = request.data
            content = data.get('content', '')
            
            # Validate word count
            word_count = len(content.split())
            if word_count > 1200:
                return Response({
                    'status': 'error',
                    'message': 'Research context exceeds 1200 words limit'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find existing context or create new one
            context, created = ResearchContext.objects.get_or_create(
                user=request.user,
                defaults={'content': content}
            )
            
            # If not created, update the existing one
            if not created:
                context.content = content
                context.save()
            
            return Response({
                'status': 'success',
                'message': 'Research context saved successfully',
                'context': {
                    'id': str(context.id),
                    'content': context.content,
                    'created_at': context.created_at,
                    'updated_at': context.updated_at
                }
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['DELETE'])
    def clear(self, request):
        """Delete the user's research context"""
        try:
            deleted, _ = ResearchContext.objects.filter(user=request.user).delete()
            
            if deleted:
                return Response({
                    'status': 'success',
                    'message': 'Research context deleted successfully'
                })
            else:
                return Response({
                    'status': 'success',
                    'message': 'No research context to delete'
                })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)