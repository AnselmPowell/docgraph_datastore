from django.contrib import admin
from django.utils.html import format_html
from django.utils.timesince import timesince
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, UserSession, LoginAttempt

# ----------------------------------------
# User Profile Admin
# ----------------------------------------

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "User Profile"
    readonly_fields = ('is_social_account', 'social_provider', 'last_login_ip', 
                      'login_count', 'last_login', 'account_created')
    
    fieldsets = (
        ('User Information', {
            'fields': ('first_name', 'last_name', 'email', 'is_email_verified')
        }),
        ('Authentication', {
            'fields': ('is_social_account', 'social_provider',)
        }),
        ('Login Statistics', {
            'fields': ('login_count', 'last_login', 'last_login_ip', 'account_created')
        }),
    )

# Extend the default UserAdmin
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 
                   'get_login_method', 'get_last_login', 'get_login_count')
    list_filter = BaseUserAdmin.list_filter + ('profile__is_social_account', 'profile__social_provider',)
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__social_provider')
    
    def get_login_method(self, obj):
        try:
            if obj.profile.is_social_account:
                return format_html(
                    '<span style="color: #0066cc;">{}</span>', 
                    obj.profile.social_provider.title()
                )
            return format_html('<span style="color: #4a6741;">Standard</span>')
        except UserProfile.DoesNotExist:
            return "N/A"
    get_login_method.short_description = 'Auth Method'
    get_login_method.admin_order_field = 'profile__is_social_account'
    
    def get_last_login(self, obj):
        try:
            if obj.profile.last_login:
                return format_html(
                    '<span title="{}">{} ago</span>',
                    obj.profile.last_login.strftime('%Y-%m-%d %H:%M:%S'),
                    timesince(obj.profile.last_login)
                )
            return "Never"
        except UserProfile.DoesNotExist:
            return "N/A"
    get_last_login.short_description = 'Last Login'
    get_last_login.admin_order_field = 'profile__last_login'
    
    def get_login_count(self, obj):
        try:
            count = obj.profile.login_count
            return count
        except UserProfile.DoesNotExist:
            return 0
    get_login_count.short_description = 'Login Count'
    get_login_count.admin_order_field = 'profile__login_count'

# Only attempt to register if not already registered
try:
    admin.site.unregister(User)
    admin.site.register(User, CustomUserAdmin)
except Exception as e:
    # Already registered or another issue - log the error
    print(f"Note: Could not register User admin: {str(e)}")

# ----------------------------------------
# Admin Site Modifications
# ----------------------------------------




# ----------------------------------------
# User Session Admin
# ----------------------------------------

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'ip_address', 'created_at', 'expires_at')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('session_token', 'refresh_token', 'device_info', 'ip_address', 
                      'created_at', 'expires_at')
    
    def has_add_permission(self, request):
        return False
    
    fieldsets = (
        ('Session Information', {
            'fields': ('user', 'is_active', 'created_at', 'expires_at')
        }),
        ('Client Information', {
            'fields': ('ip_address', 'device_info')
        }),
        ('Token Information', {
            'fields': ('session_token', 'refresh_token'),
            'classes': ('collapse',),
        }),
    )

# ----------------------------------------
# Login Attempt Admin
# ----------------------------------------

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'ip_address', 'attempt_time', 'was_successful')
    list_filter = ('was_successful', 'attempt_time')
    search_fields = ('email', 'ip_address')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False