# src/auth_api/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class UserProfile(models.Model):
    """Extended user profile information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    email = models.EmailField(max_length=150, blank=True, default="")
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    is_social_account = models.BooleanField(default=False)
    social_provider = models.CharField(max_length=50, null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    login_count = models.IntegerField(default=0)
    last_login = models.DateTimeField(null=True, blank=True)
    account_created = models.DateTimeField(auto_now_add=True)
    is_email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=255, null=True, blank=True)
    verification_token_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        provider = f" ({self.social_provider})" if self.is_social_account else ""
        return f"{self.user.email}{provider}"

    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_email_verified']),
        ]

class UserSession(models.Model):
    """User session management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    device_info = models.JSONField(null=True)
    ip_address = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.first_name}'s session"

    def is_valid(self):
        return self.is_active and self.expires_at > timezone.now()

    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_token']),
            models.Index(fields=['expires_at']),
        ]

class LoginAttempt(models.Model):
    """Track login attempts for security"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=150)
    ip_address = models.GenericIPAddressField()
    attempt_time = models.DateTimeField(auto_now_add=True)
    was_successful = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'login_attempts'
        indexes = [
            models.Index(fields=['email', 'ip_address']),
            models.Index(fields=['attempt_time']),
        ]

class PasswordReset(models.Model):
    """Password reset token management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_resets'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]
