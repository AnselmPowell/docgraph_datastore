# src/auth_api/middleware.py

from django.conf import settings
from django.http import HttpResponseForbidden
import re
from datetime import datetime, timedelta

class SecurityHeadersMiddleware:
    """Add security headers to all responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self'"
        
        return response

class IPBlocklistMiddleware:
    """Block requests from suspicious IPs"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Load blocklist from settings or database
        self.ip_blocklist = getattr(settings, 'IP_BLOCKLIST', [])

    def __call__(self, request):
        ip = self.get_client_ip(request)
        if ip in self.ip_blocklist:
            return HttpResponseForbidden('Access denied')
        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class RateLimitMiddleware:
    """Basic rate limiting"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {}

    def __call__(self, request):
        ip = self.get_client_ip(request)
        now = datetime.now()

        # Clean up old entries
        self.cleanup_old_entries(now)

        # Check rate limit
        if self.is_rate_limited(ip, now):
            return HttpResponseForbidden('Rate limit exceeded')

        # Record request
        self.record_request(ip, now)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def cleanup_old_entries(self, now):
        cutoff = now - timedelta(minutes=1)
        self.rate_limits = {
            ip: times for ip, times in self.rate_limits.items()
            if any(t > cutoff for t in times)
        }

    def is_rate_limited(self, ip, now):
        if ip not in self.rate_limits:
            return False
        
        recent_requests = len([
            t for t in self.rate_limits[ip]
            if t > now - timedelta(minutes=1)
        ])
        
        return recent_requests >= 100  # 100 requests per minute

    def record_request(self, ip, now):
        if ip not in self.rate_limits:
            self.rate_limits[ip] = []
        self.rate_limits[ip].append(now)