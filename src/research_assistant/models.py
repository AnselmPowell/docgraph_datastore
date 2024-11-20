# src/research_assistant/models.py

from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField

class DocumentMetadata(models.Model):
    """Store document metadata with citation details"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=500, null=True)
    authors = ArrayField(models.CharField(max_length=200, null=True), null=True)
    publication_date = models.DateField(null=True)
    publisher = models.CharField(max_length=200, null=True)
    doi = models.CharField(max_length=100, null=True)
    url = models.URLField(null=True, max_length=500)
    file_name = models.CharField(max_length=200, null=True)
    citation = models.TextField(null=True)
    reference = models.TextField(null=True)
    summary = models.TextField(null=True)
    total_pages = models.IntegerField(null=True)
    relevance_score = models.FloatField(default=0.0)
    relevant_sections = models.IntegerField(default=0)
    processing_status = models.CharField(
        max_length=50,
        null=True,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ]
    )
    error_message = models.TextField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'document_metadata'
        indexes = [
            models.Index(fields=['relevance_score']),
            models.Index(fields=['created_at']),
            models.Index(fields=['processing_status']),
            models.Index(fields=['last_accessed'])
        ]

class DocumentSection(models.Model):
    """Store document sections with embeddings and metadata"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=100)  # text, table, figure, etc.
    content = models.TextField()
    page_number = models.IntegerField()
    position = models.IntegerField()  # Position within page
    
    # Section pointers and metadata
    start_text = models.CharField(max_length=200)  # First 6 words
    section_id = models.CharField(max_length=100)
    url_fragment = models.CharField(max_length=200)
    
    # Content type flags
    has_citations = models.BooleanField(default=False)
    has_tables = models.BooleanField(default=False)
    has_figures = models.BooleanField(default=False)
    has_images = models.BooleanField(default=False)
    
    # Extracted content
    citations = ArrayField(models.TextField(), default=list)
    table_data = models.JSONField(null=True)
    extracted_image_text = models.TextField(null=True)
    
    # Relevance data
    relevance_type = ArrayField(models.CharField(max_length=50), default=list)
    matching_context = models.TextField(null=True)
    matching_theme = models.TextField(null=True)
    matching_keywords = ArrayField(models.TextField(), default=list)
    matching_similar_keywords = ArrayField(models.TextField(), default=list)
    
    # Vector embedding
    embedding = VectorField(dimensions=1536, null=True)
    embedding_updated = models.DateTimeField(auto_now=True, null=True)
    title_group_number = models.IntegerField(null=True)
    title_group_text = models.TextField(null=True)
    
    class Meta:
        db_table = 'document_sections'
        ordering = ['page_number', 'position']
        indexes = [
            models.Index(fields=['document', 'page_number']),
            models.Index(fields=['section_type']),
            models.Index(fields=['has_citations']),
            models.Index(fields=['embedding_updated'])
        ]

class ProcessingLog(models.Model):
    """Track document processing status and metrics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='logs')
    stage = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    message = models.TextField(null=True)
    duration = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['document', 'stage', 'timestamp']),
            models.Index(fields=['status'])
        ]

class SearchQuery(models.Model):
    """Store search queries and results"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    context = models.TextField()
    theme = models.CharField(max_length=200)
    keywords = ArrayField(models.CharField(max_length=100))
    documents = models.ManyToManyField(DocumentMetadata)
    total_results = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_queries'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['theme'])
        ]

class LLMResponseCache(models.Model):
    """Store LLM responses for caching"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='llm_responses')
    response_type = models.CharField(max_length=50)  # 'summary' or 'search'
    query_hash = models.CharField(max_length=100)
    response_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'llm_response_cache'
        indexes = [
            models.Index(fields=['document', 'response_type', 'query_hash']),
            models.Index(fields=['created_at'])
        ]
        unique_together = ['document', 'response_type', 'query_hash']