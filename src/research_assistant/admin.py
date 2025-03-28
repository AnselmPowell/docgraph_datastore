from django.contrib import admin
from django.utils.html import format_html
from django.utils.timesince import timesince
from django.contrib.auth.models import User

from .models import (
    DocumentMetadata, 
    DocumentSection, 
    SearchQuery, 
    SearchResult,
    Note,
    ResearchContext,
    LLMResponseCache,
    DocumentRelationship
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

# Initialize the admin dashboard
initialize_dashboard()