# src/auth_api/urls.py

from django.urls import path
from . import views

app_name = 'auth_api'

urlpatterns = [
    path('csrf/', views.CSRFTokenView.as_view(), name='csrf_token'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('social/auth/', views.SocialAuthView.as_view(), name='social_auth'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
]
