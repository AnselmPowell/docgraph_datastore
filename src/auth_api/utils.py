# src/auth_api/utils.py

from django.conf import settings
from datetime import datetime, timedelta
from .models import LoginAttempt
from typing import Optional

def check_login_attempts(email: str, ip_address: str) -> bool:
    """
    Check if login attempts exceed maximum allowed
    Returns True if allowed to attempt login
    """
    timeout_mins = settings.AUTH_SETTINGS['LOGIN_ATTEMPT_TIMEOUT']
    max_attempts = settings.AUTH_SETTINGS['MAX_LOGIN_ATTEMPTS']
    
    # Get recent failed attempts
    recent_attempts = LoginAttempt.objects.filter(
        email=email,
        ip_address=ip_address,
        was_successful=False,
        attempt_time__gte=datetime.now() - timedelta(minutes=timeout_mins)
    ).count()
    
    return recent_attempts < max_attempts

def log_login_attempt(email: str, ip_address: str, was_successful: bool) -> None:
    """Record a login attempt"""
    LoginAttempt.objects.create(
        email=email,
        ip_address=ip_address,
        was_successful=was_successful
    )

def get_client_ip(request) -> Optional[str]:
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')