# src/auth_api/views.py

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone

from django.contrib.auth import get_user_model
User = get_user_model()




from .models import UserProfile, UserSession, PasswordReset
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    SocialAuthSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    TokenRefreshSerializer,
    TokenResponseSerializer
)
from .authentication import TokenManager
from .utils import check_login_attempts, log_login_attempt, get_client_ip


class CSRFTokenView(APIView):
    """Get CSRF token"""
    permission_classes = [AllowAny]
    print("CSRF RETURN")

    def get(self, request):
        return JsonResponse({'csrfToken': get_token(request)})


class RegistrationView(APIView):
    """Handle user registration"""
    permission_classes = [AllowAny]

    def post(self, request):
        print("=== Registration Request ===")
        print("Request Data:", request.data)
        
        print("Request serializer:")
        serializer = UserRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid registration details',
                'detail': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        print("Done serializer:")
       
        print("=== Creating User ===")
        user = serializer.save()
        print("User created:", user.id)
        
        print("=== Generating Tokens ===")
        access_token, refresh_token = TokenManager.generate_tokens(user.id)
        print("Tokens generated successfully")
        
        print("=== Creating User Session ===")
        UserSession.objects.create(
            user=user,
            session_token=access_token,
            refresh_token=refresh_token,
            device_info=request.META.get('HTTP_USER_AGENT'),
            ip_address=get_client_ip(request),
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        print("User session created")
        
        # Create the profile data first
        profile_data = UserProfileSerializer(user.profile).data
        
        # Then create the response data
        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'user': profile_data  # Add the profile data here
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
        # except Exception as e:
        #     print("=== Error During Registration ===")
        #     print("Error:", str(e))
        #     return Response(
        #         {'error': 'Registration failed', 'detail': str(e)},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )


class LoginView(APIView):
    """Handle user login"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid credentials',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        ip_address = get_client_ip(request)

        # First check if user exists
        try:
            user = User.objects.get(email=email)
            
            # If user exists but is a social account
            if hasattr(user, 'profile') and user.profile.is_social_account:
                return Response({
                    'status': 'error',
                    'code': 'social_account',
                    'message': f'Please use {user.profile.social_provider} login for this account'
                }, status=status.HTTP_400_BAD_REQUEST)

            # If user exists, attempt authentication
            authenticated_user = authenticate(username=email, password=password)
            if not authenticated_user:
                # User exists but password is wrong
                return Response({
                    'status': 'error',
                    'code': 'invalid_password',
                    'message': 'Password is incorrect, please try again'
                }, status=status.HTTP_401_UNAUTHORIZED)

        except User.DoesNotExist:
            # No user found with this email
            return Response({
                'status': 'error',
                'code': 'user_not_found',
                'message': 'No account found with this email'
            }, status=status.HTTP_404_NOT_FOUND)
        # Check login attempts
        if not check_login_attempts(email, ip_address):
            return Response({
                'status': 'error',
                'message': 'Too many login attempts',
                'detail': 'Please wait a few minutes before trying again'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Authenticate user
        print("Start authenticate")
        user = authenticate(username=email, password=password) 
        print("Done authenticate")

        if not user:
            social_user = User.objects.filter(email=email).first()
            
            if social_user and hasattr(social_user, 'profile') and social_user.profile.is_social_account:
                return Response({
                    'status': 'error',
                    'message': 'Please use social login',
                    'detail': f'This account was created with {social_user.profile.social_provider} login'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            
            return Response({
                'status': 'error',
                'message': 'User not found',
                'detail': 'No user exists with these credentials'
            }, status=status.HTTP_404_NOT_FOUND)


        # Log successful attempt
        log_login_attempt(email, ip_address, True)
        print("-- Log successful attempt", user)
        # Generate tokens
        access_token, refresh_token = TokenManager.generate_tokens(user.id)
        print("-- Generate tokens")
        # Create or update session
        UserSession.objects.create(
            user=user,
            session_token=access_token,
            refresh_token=refresh_token,
            device_info=request.META.get('HTTP_USER_AGENT'),
            ip_address=ip_address,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        print("-- Create or update session")
        # Update user profile
        profile = user.profile
        profile.last_login = timezone.now()
        profile.last_login_ip = ip_address
        profile.login_count += 1
        profile.save()

        profile_data = UserProfileSerializer(profile).data
        # Return response directly without TokenResponseSerializer
        print("-- Return response ")
        return Response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'user': profile_data
        })

        # return Response(TokenResponseSerializer(response_data).data)


class SocialAuthView(APIView):
    """Handle social authentication"""
    permission_classes = [AllowAny]

    def post(self, request):
        print("=== Social Auth Request ===")
        print("Request Data:", request.data)
        
        serializer = SocialAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid social auth details',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        
        try:
            # Try to find existing user
            user = User.objects.filter(email=data['email']).first()
            
            if not user:
                # Create new user for social login
                user = User.objects.create(
                    username=data['email'],
                    email=data['email'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    is_active=True
                )


                user.set_unusable_password()
                user.save()
                
                # Create/update profile
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.is_social_account = True
                profile.social_provider = data['provider']
                profile.first_name =data['first_name']
                profile.last_name =data['last_name']
                profile.email =data['email']
                profile.is_email_verified = True
                profile.save()
            
            # Generate tokens
            access_token, refresh_token = TokenManager.generate_tokens(user.id)
            
            # Create session
            UserSession.objects.create(
                user=user,
                session_token=access_token,
                refresh_token=refresh_token,
                device_info=request.META.get('HTTP_USER_AGENT'),
                ip_address=get_client_ip(request),
                expires_at=timezone.now() + timezone.timedelta(days=7)
            )
            
            # Get profile data
            profile_data = UserProfileSerializer(user.profile).data
            
            return Response({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': 3600,
                'user': profile_data
            })
            
        except Exception as e:
            print("=== Error During Social Auth ===")
            print("Error:", str(e))
            return Response({
                'status': 'error',
                'message': 'Authentication failed',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# auth_api/views.py
class LogoutView(APIView):
    """Handle user logout"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("\n=== LOGOUT VIEW ===")
        print("Request User:", request.user)
        print("Request Auth:", request.auth)
        print("Request Headers:", request.headers)
        
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        print("Auth Header:", auth_header)

        # Extract token
        token_type, token = auth_header.split()
        print("Token Type:", token_type)
        print("Token:", token)

        # Find and invalidate sessions
        sessions = UserSession.objects.filter(
            user=request.user,
            session_token=token,
            is_active=True
        )
        print("Found Active Sessions:", sessions.count())
        
        # Update sessions
        updated_count = sessions.update(is_active=False)
        print("Updated Sessions Count:", updated_count)
        
        print("=== LOGOUT COMPLETE ===\n")
        
        return Response(
            {'message': 'Logged out successfully'},
            status=status.HTTP_200_OK
        )

class TokenRefreshView(APIView):
    """Handle token refresh"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        refresh_token = serializer.validated_data['refresh_token']

        try:
            # Validate refresh token
            payload = TokenManager.validate_token(refresh_token, 'refresh')
            user_id = payload['user_id']

            # Generate new tokens
            access_token, new_refresh_token = TokenManager.generate_tokens(user_id)

            # Update session
            session = UserSession.objects.get(
                user_id=user_id,
                refresh_token=refresh_token,
                is_active=True
            )
            session.refresh_token = new_refresh_token
            session.save()

            return Response({
                'access_token': access_token,
                'refresh_token': new_refresh_token,
                'token_type': 'Bearer',
                'expires_in': 3600
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        print(f"[UserProfileView] Fetching profile for user: {request.user.email}")
        
        try:
            # Get user and document counts
            document_count = request.user.documents.count()
            search_count = request.user.search_queries.count()
            
            user_data = {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'stats': {
                    'document_count': document_count,
                    'search_count': search_count,
                    'last_login': request.user.last_login,
                }
            }
            
            print(f"[UserProfileView] Profile data: {user_data}")
            return Response(user_data)
            
        except Exception as e:
            print(f"[UserProfileView] Error: {str(e)}")
            return Response(
                {'error': 'Failed to fetch user profile'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordChangeView(APIView):
    """Handle password change"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Verify old password
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response({'message': 'Password updated successfully'})