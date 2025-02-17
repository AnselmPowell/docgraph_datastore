# src/auth_api/authentication.py
import jwt as PyJWT  
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from .models import UserSession

class TokenManager:
    """Handles JWT token generation and validation"""
    
    @staticmethod
    def generate_tokens(user_id: int) -> tuple[str, str]:
        """Generate access and refresh tokens"""
        
        # Access token - short lived
        access_token = PyJWT.encode(
            {
                'user_id': user_id,
                'type': 'access',
                'exp': datetime.utcnow() + settings.JWT_SETTINGS['ACCESS_TOKEN_LIFETIME'],
                'iat': datetime.utcnow()
            }, 
            settings.JWT_SETTINGS['SIGNING_KEY'],
            algorithm=settings.JWT_SETTINGS['ALGORITHM']
        )

        # Refresh token - long lived
        refresh_token = PyJWT.encode(
            {
                'user_id': user_id,
                'type': 'refresh',
                'exp': datetime.utcnow() + settings.JWT_SETTINGS['REFRESH_TOKEN_LIFETIME'],
                'iat': datetime.utcnow()
            }, 
            settings.JWT_SETTINGS['SIGNING_KEY'],
            algorithm=settings.JWT_SETTINGS['ALGORITHM']
        )

        return access_token, refresh_token

    @staticmethod
    def validate_token(token: str, token_type: str = 'access') -> dict:
        """Validate JWT token and return payload"""
        try:
            payload = PyJWT.decode(
                token, 
                settings.JWT_SETTINGS['SIGNING_KEY'],
                algorithms=[settings.JWT_SETTINGS['ALGORITHM']]
            )

            # Verify token type
            if payload.get('type') != token_type:
                raise exceptions.AuthenticationFailed('Invalid token type')

            return payload
        except PyJWT.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except PyJWT.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        

class JWTAuthentication(authentication.BaseAuthentication):
   """Custom JWT authentication for DRF"""
   
   def authenticate(self, request):
       # Get token from header
       auth_header = request.headers.get('Authorization')
       if not auth_header:
           return None
           
       try:
           # Extract the token
           header_parts = auth_header.split()
           if len(header_parts) != 2 or header_parts[0].lower() != 'bearer':
               raise exceptions.AuthenticationFailed('Invalid token header')

           token = header_parts[1]

           # Validate token
           payload = TokenManager.validate_token(token)
           
           # Get user from token payload
           user = User.objects.filter(id=payload['user_id']).first()
           if not user:
               raise exceptions.AuthenticationFailed('User not found')

           # Check if user session is valid
           session = UserSession.objects.filter(
               user=user,
               session_token=token,
               is_active=True,
               expires_at__gt=datetime.now()
           ).first()

           if not session:
               raise exceptions.AuthenticationFailed('Invalid or expired session')

           return (user, token)

       except Exception as e:
           raise exceptions.AuthenticationFailed(str(e))

   def authenticate_header(self, request):
       """Return string to be used as the value of the WWW-Authenticate header"""
       return 'Bearer'