
# research_assistant/models.py
# models.py
from django.db import models
import uuid
import json
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User 

class DocumentMetadata(models.Model):    
    """Store document metadata with processing status"""
    # This model stays largely the same as it contains core metadata
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    title = models.CharField(max_length=500, null=True)
    authors = models.JSONField(null=True, default=list)
    publication_date = models.DateField(null=True)
    publisher = models.CharField(max_length=200, null=True)
    doi = models.CharField(max_length=100, null=True)
    url = models.URLField(null=True, max_length=500)
    file_name = models.CharField(max_length=200, null=True)
    citation = models.CharField(max_length=800, null=True)
    reference = models.JSONField(null=True, default=dict)
    summary = models.TextField(null=True)
    total_pages = models.IntegerField(null=True)
    
    processing_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    processing_progress = models.FloatField(default=0.0)
    processing_stage = models.CharField(max_length=100, null=True)
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        """Check if document is older than 30 days"""
        if not self.created_at:
            return False
        expiration_date = self.created_at + timedelta(days=30)
        return timezone.now() > expiration_date
    

    @classmethod
    def delete_expired(cls):
        """Delete all documents older than 30 days"""
        expiration_cutoff = timezone.now() - timedelta(days=30)
        expired_docs = cls.objects.filter(created_at__lt=expiration_cutoff)
        
        # Get count before deletion for logging
        count = expired_docs.count()
        
        # Django will handle cascade deletion for related models
        deleted = expired_docs.delete()
        
        return count

    class Meta:
        db_table = 'document_metadata'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['processing_status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at'])
        ]

class DocumentSection(models.Model):
    """Store document sections with metadata"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=100)  # 'text', 'table', 'image'
    content = models.TextField()  # Main page content
    section_start_page_number = models.IntegerField()
    
    # Context text from adjacent pages
    prev_page_text = models.TextField(null=True)
    next_page_text = models.TextField(null=True)
    
    # Content flags
    has_citations = models.BooleanField(default=False)
    has_tables = models.BooleanField(default=False)
    has_images = models.BooleanField(default=False)
    
    # Content data
    citations = models.JSONField(default=dict)
    tables = models.JSONField(null=True)  # Store table data
    images = models.JSONField(default=list)  # Store image metadata
    
    class Meta:
        db_table = 'document_sections'
        ordering = ['section_start_page_number']
        indexes = [
            models.Index(fields=['document', 'section_start_page_number']),
            models.Index(fields=['section_type'])
        ]

    def set_elements(self, elements_list):
        """Transform and set tables and images data"""
        print(f"[DocumentSection] Processing {len(elements_list)} elements")
        
        tables = []
        images = []
        
        for element in elements_list:
            try:
                if isinstance(element, dict):
                    if element.get('type') == 'table':
                        tables.append(element.get('content'))
                    elif element.get('type') == 'image':
                        images.append(element.get('metadata'))
                
            except Exception as e:
                print(f"[DocumentSection] Error processing element: {str(e)}")
                continue
            
        self.tables = tables if tables else None
        self.images = images
        
    def get_elements(self):
        """Get combined elements data"""
        elements = []
        
        # Add tables
        if self.tables:
            elements.extend([{'type': 'table', 'content': table} for table in self.tables])
            
        # Add images
        if self.images:
            elements.extend([{'type': 'image', 'metadata': img} for img in self.images])
            
        return elements


class SearchQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='search_queries',
        null=True,
        blank=True
    )
    documents = models.ManyToManyField(DocumentMetadata, related_name='searches')
    context = models.TextField()
    keywords = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'search_queries'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at'])
        ]




class SearchResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_results')
    document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE)
    
    # Search Parameters
    query_context = models.TextField()
    keywords = models.JSONField(default=list)
    
    # Results Data
    document_title = models.CharField(max_length=500)
    document_authors = models.JSONField(default=list)
    document_summary = models.TextField(null=True)
    relevance_score = models.FloatField()
    
    # Add processing status field
    processing_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    error_message = models.TextField(null=True, blank=True)
    
    # Matching Sections
    matching_sections = models.JSONField(default=list)
    # Structure for matching_sections:
    # [{
    #     'section_id': str,
    #     'page_number': int,
    #     'content': str,
    #     'context_matches': [{
    #         'text': str,
    #         'citations': list
    #     }],
    #     'keyword_matches': [{
    #         'keyword': str,
    #         'text': str
    #     }],
    #     'similar_matches': [{
    #         'similar_keyword': str,
    #         'text': str
    #     }]
    # }]
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'search_results'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['document']),
            models.Index(fields=['created_at']),
            models.Index(fields=['relevance_score']),
            models.Index(fields=['processing_status'])  # Add index for status
        ]



class Note(models.Model):
    """Store user notes with references to documents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    
    # Note content
    title = models.CharField(max_length=500)
    content = models.TextField()
    
    # Document metadata
    document_id = models.CharField(max_length=500, null=True, blank=True)
    page_number = models.IntegerField(null=True, blank=True)
    source = models.CharField(max_length=500, null=True, blank=True)
    
    # Citations and references stored as JSON
    citations = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['document_id'])
        ]
    
    def __str__(self):
        return f"Note: {self.title[:50]}"
    


class ResearchContext(models.Model):
    """Store user research context - only one per user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='research_context')
    content = models.TextField()  # Will store up to 1200 words of context
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'research_contexts'
        # Enforce one context per user
        constraints = [
            models.UniqueConstraint(fields=['user'], name='one_context_per_user')
        ]
    
    def __str__(self):
        return f"Research Context for {self.user.username}"



class LiteratureReview(models.Model):
    """Store structured literature review data extracted from documents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='literature_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='literature_reviews', null=True, blank=True)
    
    # Literature review data
    research_area =  models.JSONField(default=dict)
    themes = models.JSONField(default=list)
    chronological_development =  models.JSONField(default=dict)
    theoretical_frameworks =  models.JSONField(default=dict)
    methodological_approaches = models.JSONField(default=dict)
    key_findings = models.JSONField(default=list)
    method_strengths = models.JSONField(default=list)
    method_limitations = models.JSONField(default=list)
    result_strengths = models.JSONField(default=list)
    result_weaknesses = models.JSONField(default=list)
    potential_biases = models.JSONField(default=list)
    
    # Processing metadata
    extraction_time = models.FloatField(null=True)
    processing_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'literature_reviews'
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['user']),
            models.Index(fields=['processing_status']),
            models.Index(fields=['created_at'])
        ]
        
    def __str__(self):
        return f"Literature Review for {self.document.title or self.document.file_name}"





        
class LLMResponseCache(models.Model):
    """Store LLM responses for caching"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey( User, on_delete=models.CASCADE, related_name='llm_responses', null=True,  blank=True)
    file_name = models.CharField(max_length=200, null=True)
    document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='llm_responses')
    response_type = models.CharField(max_length=50)  # 'summary' or 'search'
    query_hash = models.TextField()
    response_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'llm_response_cache'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['document', 'response_type', 'query_hash']),
            models.Index(fields=['created_at'])
        ]
        unique_together = ['user', 'document', 'response_type', 'query_hash']

class DocumentRelationship(models.Model):
    """Track relationships between documents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    source_document = models.ForeignKey(
        DocumentMetadata,
        on_delete=models.CASCADE,
        related_name='source_relationships'
    )
    target_document = models.ForeignKey(
        DocumentMetadata,
        on_delete=models.CASCADE,
        related_name='target_relationships'
    )
    relationship_type = models.CharField(max_length=100)  # e.g., 'citation', 'keyword'
    confidence_score = models.FloatField()
    metadata = models.JSONField(default=dict)  # Store relationship details
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_relationships'
        indexes = [
            models.Index(fields=['source_document', 'target_document']),
            models.Index(fields=['relationship_type']),
            models.Index(fields=['confidence_score'])
        ] 








class AIAPIUsage(models.Model):
    """Track AI API usage and costs for searches"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_usages', null=True)
    search_result = models.ForeignKey(SearchResult, on_delete=models.CASCADE, related_name='api_usages', null=True)
    document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='api_usages', null=True)
    
    # API Call Details
    model_name = models.CharField(max_length=100)  # e.g., 'gpt-4-mini', 'gpt-3.5-turbo'
    prompt = models.TextField(null=True)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    
    # Cost Tracking
    cost_per_1k_prompt_tokens = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    cost_per_1k_completion_tokens = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Performance Tracking
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    duration_ms = models.IntegerField(default=0)
    
    # Aggregation Fields
    is_aggregated = models.BooleanField(default=False)
    api_calls_count = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_api_usage'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['search_result']),
            models.Index(fields=['model_name']),
            models.Index(fields=['created_at'])
        ]