# # src/research_assistant/models.py
 
# from django.db import models
# import uuid
# from django.contrib.postgres.fields import ArrayField
# from pgvector.django import VectorField

# class DocumentMetadata(models.Model):
#     """Store document metadata with citation details"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     title = models.CharField(max_length=500, null=True)
#     authors = ArrayField(models.CharField(max_length=200, null=True), null=True)
#     publication_date = models.DateField(null=True)
#     publisher = models.CharField(max_length=200, null=True)
#     doi = models.CharField(max_length=100, null=True)
#     url = models.URLField(null=True, max_length=500)
#     file_name = models.CharField(max_length=200, null=True)
#     citation = models.TextField(null=True)
#     reference = models.TextField(null=True)
#     summary = models.TextField(null=True)
#     total_pages = models.IntegerField(null=True)
#     relevance_score = models.FloatField(default=0.0)
#     relevant_sections = models.IntegerField(default=0)
#     processing_status = models.CharField(
#         max_length=50,
#         null=True,
#         default='pending',
#         choices=[
#             ('pending', 'Pending'),
#             ('processing', 'Processing'),
#             ('completed', 'Completed'),
#             ('failed', 'Failed')
#         ]
#     )
#     error_message = models.TextField(null=True, blank=True)
#     last_accessed = models.DateTimeField(auto_now=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         db_table = 'document_metadata'
#         indexes = [
#             models.Index(fields=['relevance_score']),
#             models.Index(fields=['created_at']),
#             models.Index(fields=['processing_status']),
#             models.Index(fields=['last_accessed'])
#         ]

# class DocumentSection(models.Model):
#     """Store document sections with embeddings and metadata"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='sections')
#     section_type = models.CharField(max_length=100)  # text, table, figure, etc.
#     content = models.TextField()
#     section_start_page_number = models.IntegerField()
#     position = models.IntegerField()  # Position within page
    
#     # Section pointers and metadata
#     start_text = models.CharField(max_length=200)  # First 6 words
#     section_id = models.CharField(max_length=100)
#     url_fragment = models.CharField(max_length=200)
    
#     # Content type flags
#     has_citations = models.BooleanField(default=False)
#     has_tables = models.BooleanField(default=False)
#     has_figures = models.BooleanField(default=False)
#     has_images = models.BooleanField(default=False)
    
#     # Extracted content
#     citations = ArrayField(models.TextField(), default=list)
#     table_data = models.JSONField(null=True)
#     extracted_image_text = models.TextField(null=True)
#     elements = models.JSONField(
#         default=list,
#         null=True,
#     )
    
#     # Relevance data
#     relevance_type = ArrayField(models.CharField(max_length=50), default=list)
#     matching_context = models.TextField(null=True)
#     matching_theme = models.TextField(null=True)
#     matching_keywords = ArrayField(models.TextField(), default=list)
#     matching_similar_keywords = ArrayField(models.TextField(), default=list)
    
#     # Vector embedding
#     embedding = VectorField(dimensions=1536, null=True)
#     embedding_updated = models.DateTimeField(auto_now=True, null=True)
#     title_group_number = models.IntegerField(null=True)
#     title_group_text = models.TextField(null=True)
    
#     class Meta:
#         db_table = 'document_sections'
#         ordering = ['section_start_page_number', 'position']
#         indexes = [
#             models.Index(fields=['document', 'section_start_page_number']),
#             models.Index(fields=['section_type']),
#             models.Index(fields=['has_citations']),
#             models.Index(fields=['embedding_updated'])
#         ]


# class SearchQuery(models.Model):
#     """Store search queries and results"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     context = models.TextField()
#     theme = models.CharField(max_length=200)
#     keywords = ArrayField(models.CharField(max_length=100))
#     documents = models.ManyToManyField(DocumentMetadata)
#     total_results = models.IntegerField()
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         db_table = 'search_queries'
#         indexes = [
#             models.Index(fields=['created_at']),
#             models.Index(fields=['theme'])
#         ]

# class LLMResponseCache(models.Model):
#     """Store LLM responses for caching"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='llm_responses')
#     response_type = models.CharField(max_length=50)  # 'summary' or 'search'
#     query_hash = models.TextField()
#     response_data = models.JSONField()
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         db_table = 'llm_response_cache'
#         indexes = [
#             models.Index(fields=['document', 'response_type', 'query_hash']),
#             models.Index(fields=['created_at'])
#         ]
#         unique_together = ['document', 'response_type', 'query_hash']


































# # src/research_assistant/models.py
# from django.db import models
# import uuid
# import json

# class JSONField(models.TextField):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#     def from_db_value(self, value, expression, connection):
#         if value is None:
#             return None
#         return json.loads(value)

#     def to_python(self, value):
#         if isinstance(value, (list, dict)):
#             return value
#         if value is None:
#             return None
#         return json.loads(value)

#     def get_prep_value(self, value):
#         if value is None:
#             return None
#         return json.dumps(value)

# class DocumentMetadata(models.Model):
#     """Store document metadata with citation details"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     title = models.CharField(max_length=500, null=True)
    
#     authors = JSONField(null=True, default=list)
    
#     publication_date = models.DateField(null=True)
#     publisher = models.CharField(max_length=200, null=True)
#     doi = models.CharField(max_length=100, null=True)
#     url = models.URLField(null=True, max_length=500)
#     file_name = models.CharField(max_length=200, null=True)
#     citation = models.TextField(null=True)
#     reference = JSONField(null=True,default=dict(
#         entries={},
#         type="",
#         start_page=None,
#         end_page=None,
#         start_index=0,
#         end_index=0
#     ))
#     summary = models.TextField(null=True)
#     total_pages = models.IntegerField(null=True)
#     relevance_score = models.FloatField(default=0.0)
#     relevant_sections = models.IntegerField(default=0)
#     processing_status = models.CharField(
#         max_length=50,
#         null=True,
#         default='pending',
#         choices=[
#             ('pending', 'Pending'),
#             ('processing', 'Processing'),
#             ('completed', 'Completed'),
#             ('failed', 'Failed')
#         ]
#     )
#     error_message = models.TextField(null=True, blank=True)
#     last_accessed = models.DateTimeField(auto_now=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'document_metadata'
#         indexes = [
#             models.Index(fields=['relevance_score']),
#             models.Index(fields=['created_at']),
#             models.Index(fields=['processing_status']),
#             models.Index(fields=['last_accessed'])
#         ]

# class DocumentSection(models.Model):
#     """Store document sections with metadata"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='sections')
#     section_type = models.CharField(max_length=100)
#     content = models.TextField()
#     section_start_page_number = models.IntegerField()
#     position = models.IntegerField()
    
#     start_text = models.CharField(max_length=200)
#     section_id = models.CharField(max_length=100)
#     url_fragment = models.CharField(max_length=200)
    
#     has_citations = models.BooleanField(default=False)
#     has_tables = models.BooleanField(default=False)
#     has_figures = models.BooleanField(default=False)
#     has_images = models.BooleanField(default=False)
    
#     # Changed all ArrayFields to JSONField
#     citations = JSONField(default=dict)
#     table_data = JSONField(null=True)
#     extracted_image_text = models.TextField(null=True)
#     elements = JSONField(default=list)
    
#     relevance_type = JSONField(default=dict)
#     matching_context = models.TextField(null=True)
#     matching_theme = models.TextField(null=True)
#     matching_keywords = JSONField(default=dict)
#     matching_similar_keywords = JSONField(default=dict)
    
#     # Changed embedding to JSONField
#     embedding = JSONField(null=True)
#     embedding_updated = models.DateTimeField(auto_now=True, null=True)
#     title_group_number = models.IntegerField(null=True)
#     title_group_text = models.TextField(null=True)
    
#     class Meta:
#         db_table = 'document_sections'
#         ordering = ['section_start_page_number', 'position']
#         indexes = [
#             models.Index(fields=['document', 'section_start_page_number']),
#             models.Index(fields=['section_type']),
#             models.Index(fields=['has_citations'])
#         ]
    
#     def set_elements(self, elements_list):
#         """Transform and set elements data for storage"""
#         transformed_elements = []
        
#         for element in elements_list:
#             # Extract relevant data from CompositeElement
#             element_dict = {
#                 'id': element.id,
#                 'text': element.text,
#                 'category': element.category,
#                 # Convert metadata to dict
#                 'metadata': {
#                     'page_number': element.metadata.page_number if hasattr(element.metadata, 'page_number') else None,
#                     'filename': element.metadata.filename if hasattr(element.metadata, 'filename') else None,
#                 }
#             }
#             transformed_elements.append(element_dict)
            
#         self.elements = transformed_elements
        
#     def get_elements(self):
#         """Retrieve stored elements data"""
#         return self.elements






# # research_assistant/models.py

# from django.db import models
# import uuid
# import json

# class DocumentMetadata(models.Model):
#     """Store document metadata with processing status"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     title = models.CharField(max_length=500, null=True)
#     authors = models.JSONField(null=True, default=list)
#     publication_date = models.DateField(null=True)
#     publisher = models.CharField(max_length=200, null=True)
#     doi = models.CharField(max_length=100, null=True)
#     url = models.URLField(null=True, max_length=500)
#     file_name = models.CharField(max_length=200, null=True)
#     citation = models.TextField(null=True)
#     reference = models.JSONField(null=True, default=dict)
#     summary = models.TextField(null=True)
#     total_pages = models.IntegerField(null=True)
    
#     # New fields for processing status
#     processing_status = models.CharField(
#         max_length=50,
#         choices=[
#             ('pending', 'Pending'),
#             ('processing', 'Processing'),
#             ('completed', 'Completed'),
#             ('failed', 'Failed')
#         ],
#         default='pending'
#     )
#     processing_progress = models.FloatField(default=0.0)
#     processing_stage = models.CharField(max_length=100, null=True)
#     error_message = models.TextField(null=True, blank=True)
    
#     # Timestamps
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = 'document_metadata'
#         indexes = [
#             models.Index(fields=['processing_status']),
#             models.Index(fields=['created_at']),
#             models.Index(fields=['updated_at'])
#         ]

# class DocumentSection(models.Model):
#     """Store document sections with metadata"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='sections')
#     section_type = models.CharField(max_length=100)
#     content = models.TextField()
#     section_start_page_number = models.IntegerField()
#     position = models.IntegerField()
    
#     # Section metadata
#     title_group_number = models.IntegerField(null=True)
#     title_group_text = models.TextField(null=True)
#     start_text = models.CharField(max_length=200)
#     section_id = models.CharField(max_length=100)
#     url_fragment = models.CharField(max_length=200)
    
#     # Section content flags
#     has_citations = models.BooleanField(default=False)
#     has_tables = models.BooleanField(default=False)
#     has_figures = models.BooleanField(default=False)
#     has_images = models.BooleanField(default=False)
    
#     # Section content data
#     citations = models.JSONField(default=dict)
#     table_data = models.JSONField(null=True)
#     elements = models.JSONField(default=list)
    
#     class Meta:
#         db_table = 'document_sections'
#         ordering = ['section_start_page_number', 'position']
#         indexes = [
#             models.Index(fields=['document', 'section_start_page_number']),
#             models.Index(fields=['section_type'])
#         ]


# class LLMResponseCache(models.Model):
#     """Store LLM responses for caching"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='llm_responses')
#     response_type = models.CharField(max_length=50)  # 'summary' or 'search'
#     query_hash = models.TextField()
#     response_data = models.JSONField()
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         db_table = 'llm_response_cache'
#         indexes = [
#             models.Index(fields=['document', 'response_type', 'query_hash']),
#             models.Index(fields=['created_at'])
#         ]
#         unique_together = ['document', 'response_type', 'query_hash']


































# research_assistant/models.py
from django.db import models
import uuid
import json

class DocumentMetadata(models.Model):
    """Store document metadata with processing status"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=500, null=True)
    authors = models.JSONField(null=True, default=list)
    publication_date = models.DateField(null=True)
    publisher = models.CharField(max_length=200, null=True)
    doi = models.CharField(max_length=100, null=True)
    url = models.URLField(null=True, max_length=500)
    file_name = models.CharField(max_length=200, null=True)
    citation = models.TextField(null=True)
    reference = models.JSONField(null=True, default=dict)
    summary = models.TextField(null=True)
    total_pages = models.IntegerField(null=True)
    
    # Processing status fields
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
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'document_metadata'
        indexes = [
            models.Index(fields=['processing_status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at'])
        ]

class DocumentSection(models.Model):
    """Store document sections with metadata"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=100)
    content = models.TextField()
    section_start_page_number = models.IntegerField()
    position = models.IntegerField()
    
    # Section metadata
    title_group_number = models.IntegerField(null=True)
    title_group_text = models.TextField(null=True)
    start_text = models.CharField(max_length=200)
    section_id = models.CharField(max_length=100)
    url_fragment = models.CharField(max_length=200)
    
    # Content flags
    has_citations = models.BooleanField(default=False)
    has_tables = models.BooleanField(default=False)
    has_figures = models.BooleanField(default=False)
    has_images = models.BooleanField(default=False)
    
    # Content data
    citations = models.JSONField(default=dict)
    table_data = models.JSONField(null=True)
    elements = models.JSONField(default=list)
    extracted_image_text = models.TextField(null=True)
    
    class Meta:
        db_table = 'document_sections'
        ordering = ['section_start_page_number', 'position']
        indexes = [
            models.Index(fields=['document', 'section_start_page_number']),
            models.Index(fields=['section_type'])
        ]

    def set_elements(self, elements_list):
        """Transform and set elements data for storage"""
        print(f"[DocumentSection] Transforming {len(elements_list)} elements")
        transformed_elements = []
        
        for element in elements_list:
            try:
                # Handle both dict and object element formats
                if isinstance(element, dict):
                    element_dict = element
                else:
                    # Extract relevant data from CompositeElement
                    element_dict = {
                        'id': getattr(element, 'id', None),
                        'text': getattr(element, 'text', ''),
                        'category': getattr(element, 'category', None),
                        'metadata': {}
                    }
                    
                    # Handle metadata
                    if hasattr(element, 'metadata'):
                        metadata = element.metadata
                        element_dict['metadata'] = {
                            'page_number': getattr(metadata, 'page_number', None),
                            'filename': getattr(metadata, 'filename', None),
                        }

                transformed_elements.append(element_dict)
                print(f"[DocumentSection] Transformed element: {element_dict['id']}")
                
            except Exception as e:
                print(f"[DocumentSection] Error transforming element: {str(e)}")
                continue
            
        self.elements = transformed_elements
        
    def get_elements(self):
        """Retrieve stored elements data"""
        return self.elements

class SearchQuery(models.Model):
    """Store search queries and parameters"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    documents = models.ManyToManyField(DocumentMetadata, related_name='searches')
    context = models.TextField()
    theme = models.CharField(max_length=200)
    keywords = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'search_queries'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['theme'])
        ]

class SearchResult(models.Model):
    """Store search results with relevance scores"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    search_query = models.ForeignKey(SearchQuery, on_delete=models.CASCADE, related_name='results')
    document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE)
    relevance_score = models.FloatField()
    matching_sections = models.JSONField(default=list)  # List of matching section IDs with scores
    context_matches = models.JSONField(default=list)
    theme_matches = models.JSONField(default=list)
    keyword_matches = models.JSONField(default=list)
    citation_matches = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'search_results'
        indexes = [
            models.Index(fields=['search_query', 'document']),
            models.Index(fields=['relevance_score']),
            models.Index(fields=['created_at'])
        ]

class LLMResponseCache(models.Model):
    """Store LLM responses for caching"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='llm_responses')
    response_type = models.CharField(max_length=50)  # 'summary' or 'search'
    query_hash = models.TextField()
    response_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'llm_response_cache'
        indexes = [
            models.Index(fields=['document', 'response_type', 'query_hash']),
            models.Index(fields=['created_at'])
        ]
        unique_together = ['document', 'response_type', 'query_hash']

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
    relationship_type = models.CharField(max_length=100)  # e.g., 'citation', 'theme', 'keyword'
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