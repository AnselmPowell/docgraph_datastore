from django.contrib import admin
from django.utils.html import format_html
from django.utils.timesince import timesince
from django.contrib.auth.models import User
from django.urls import reverse, path
from django.http import HttpResponseRedirect

from .models import (
    DocumentMetadata, 
    DocumentSection, 
    SearchQuery, 
    SearchResult,
    Note,
    ResearchContext,
    LLMResponseCache,
    DocumentRelationship,
    AIAPIUsage 
)

from .admin_dashboard import initialize_dashboard

# Register models with admin site
@admin.register(DocumentMetadata)
class DocumentMetadataAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_name', 'get_user', 'created_at', 'processing_status', 'total_pages')
    list_filter = ('processing_status', 'created_at')
    search_fields = ('title', 'file_name', 'user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def get_user(self, obj):
        if obj.user:
            return obj.user.email
        return "No User"
    get_user.short_description = 'User'
    get_user.admin_order_field = 'user__email'
    
    fieldsets = (
        ('Document Information', {
            'fields': ('id', 'title', 'file_name', 'user', 'url')
        }),
        ('Metadata', {
            'fields': ('authors', 'publication_date', 'publisher', 'doi', 'citation')
        }),
        ('Content', {
            'fields': ('summary', 'total_pages')
        }),
        ('Processing', {
            'fields': ('processing_status', 'processing_progress', 'processing_stage', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    list_display = ('query_context_summary', 'document_title', 'get_user', 'relevance_score', 'processing_status', 'created_at')
    list_filter = ('processing_status', 'created_at', 'relevance_score')
    search_fields = ('query_context', 'document_title', 'user__username', 'user__email')
    readonly_fields = ('id', 'created_at')
    
    def query_context_summary(self, obj):
        if len(obj.query_context) > 50:
            return f"{obj.query_context[:50]}..."
        return obj.query_context
    query_context_summary.short_description = 'Query'
    
    def get_user(self, obj):
        if obj.user:
            return obj.user.email
        return "No User"
    get_user.short_description = 'User'
    get_user.admin_order_field = 'user__email'

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'content', 'user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def get_user(self, obj):
        if obj.user:
            return obj.user.email
        return "No User"
    get_user.short_description = 'User'
    get_user.admin_order_field = 'user__email'

@admin.register(AIAPIUsage)
class AIAPIUsageAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'get_user', 'model_name', 'total_tokens', 
                   'prompt_tokens', 'completion_tokens', 'total_cost', 'duration_ms', 'is_aggregated', 'view_dashboard')
    list_filter = ('model_name', 'is_aggregated', 'created_at')
    search_fields = ('user__username', 'user__email', 'model_name', 'prompt')
    
    def get_user(self, obj):
        if obj.user:
            return obj.user.email
        return "No User"
    get_user.short_description = 'User'
    get_user.admin_order_field = 'user__email'
    
    def view_dashboard(self, obj):
        """Add a direct dashboard link in the admin list view"""
        return format_html('<a class="button" href="/admin/ai-dashboard/">View AI Dashboard</a>')
    view_dashboard.short_description = "Dashboard"

    actions = ['view_ai_dashboard']
    
    def view_ai_dashboard(self, request, queryset):
        """Admin action to go to dashboard"""
        print("[view_ai_dashboard] Redirecting to dashboard view")
        return HttpResponseRedirect('/admin/ai-dashboard/')
    view_ai_dashboard.short_description = "View AI Usage Dashboard"
    


# Initialize the admin dashboard
initialize_dashboard()