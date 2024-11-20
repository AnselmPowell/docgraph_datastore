# src/research_assistant/services/document_summarizer.py
from typing import Dict
from openai import OpenAI
from django.conf import settings
import json
from pydantic import BaseModel, Field
import re
from datetime import datetime

from .monitoring.system_monitor import AIModelCosts
from .cache_manager import DocumentCacheManager

class MetadataSchema(BaseModel):
    """Schema for document metadata extraction"""
    title: str = Field(..., description="Document title")
    authors: list[str] = Field(..., description="List of authors")
    publication_date: str = Field(None, description="Publication date if available")
    publisher: str = Field(None, description="Publisher name if available") 
    doi: str = Field(None, description="DOI if available")
    citation: str = Field(..., description="Full citation in academic format")
    reference: str = Field(..., description="Full reference entry")
    summary: str = Field(..., description="2-3 sentence summary")
    total_pages: int = Field(default=1, description="Total number of pages")

class DocumentSummarizer:
    """Generate document summary and extract metadata"""
    
    def __init__(self):
        self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
        print("[DocumentSummarizer] Initialized with monitoring")
        self.cache_manager = DocumentCacheManager()  # Add this
        print("[DocumentSummarizer] Initialized with cache manager")

    def _construct_prompt(self, text: str) -> str:
        """Construct metadata extraction prompt"""
        
        print(f"[DocumentSummarizer] Constructing prompt for text length: {len(text)}")
        
        prompt = f"""
        Academic Document Text:
        {text[:1000]}... 

        \n#####

        Above is the text from a academic document, please analyze the following academic document text and extract key metadata.
        Focus on identifying:
        1. Title (required)
        2. Authors (required)
        3. Publication date (if available, format: YYYY-MM-DD)
        4. Publisher (if available)
        5. DOI (if available)
        6. Generate proper academic citation (required)
        7. Create full reference entry (required) HARDVARD REFERENCE FORMAT
        8. Write 2-3 sentence summary of main topic/findings (required)
        9. Total pages (default to 1 if not found)
        
        Extract ALL available information but leave optional fields empty if not found.
        Ensure citation and reference follow academic format standards.
        For missing dates, use logical inference from content or citations if possible.

        Respond in JSON format matching the MetadataSchema.
        """
        print(f"[DocumentSummarizer] Prompt constructed, length: {len(prompt)}")
        return prompt

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        print(f"[DocumentSummarizer] Cleaning text, original length: {len(text)}")
        
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        print(f"[DocumentSummarizer] Text cleaned, new length: {len(text)}")
        return text

    def _parse_date(self, date_str: str) -> str:
        """Parse and validate publication date"""
        if not date_str:
            print("[DocumentSummarizer] No date provided")
            return None
            
        print(f"[DocumentSummarizer] Attempting to parse date: {date_str}")
        
        # Handle various date formats
        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%Y'):
            print(f"[DocumentSummarizer] Trying format: {fmt}")
            parsed_date = None
            
            if parsed_date := self._try_parse_date(date_str, fmt):
                print(f"[DocumentSummarizer] Successfully parsed date: {parsed_date}")
                return parsed_date
        
        print(f"[DocumentSummarizer] Failed to parse date: {date_str}")
        return None

    def _try_parse_date(self, date_str: str, fmt: str) -> str:
        """Helper function to try parsing a date with a specific format"""
        print(f"[DocumentSummarizer] Attempting format {fmt} for date: {date_str}")
        
        parsed_date = None
        if isinstance(date_str, str):
            print(f"[DocumentSummarizer] Validated date string format")
            parsed_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            print(f"[DocumentSummarizer] Date parsed: {parsed_date}")
            
        return parsed_date

    def generate_summary(self, text: str, document_id: str) -> Dict:
        """Generate document summary and extract metadata"""
        print("[DocumentSummarizer] Starting document summary generation")
        
        # Check cache first
        query_data = {
            'text_preview': text[:1000],
            'type': 'summary'
        }
        query_hash = self.cache_manager.generate_query_hash(query_data)
        print(f"[DocumentSummarizer] Query hash: {query_hash}")
        
        cached_summary = self.cache_manager.get_llm_response_sync(
            document_id=document_id,
            response_type='summary',
            query_hash=query_hash  # Use the already generated hash
        )
        
        print(f"[DocumentSummarizer] Cached summary: {cached_summary}")
        if cached_summary:
            print("[DocumentSummarizer] Using cached summary: \n \n \n", cached_summary )
            return cached_summary

        # If no cache, proceed with normal summary generation
        cleaned_text = self._clean_text(text)
        print(f"[DocumentSummarizer] Text cleaned and ready for analysis")
        
        function_schema = {
            "name": "extract_document_metadata",
            "parameters": MetadataSchema.schema()
        }
        
        print("[DocumentSummarizer] Calling OpenAI API for metadata extraction")
        response = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": self._construct_prompt(cleaned_text)
            }],
            temperature=0.3,
            functions=[function_schema],
            function_call={"name": "extract_document_metadata"}
        )
        
        metadata = json.loads(response.choices[0].message.function_call.arguments)
        
        # Process publication date if present
        if metadata.get('publication_date'):
            metadata['publication_date'] = self._parse_date(metadata['publication_date'])
        
        # Store in cache
        self.cache_manager.store_llm_response_sync(
            document_id=document_id,
            response_type='summary',
            query_hash=query_hash,
            response_data=metadata
        )

        print("[DocumentSummarizer] Metadata extraction complete")
        print(f"[DocumentSummarizer] Found {len(metadata)} metadata fields")
        print(f"[DocumentSummarizer] Title: {metadata.get('title', 'Not found')}")
        print(f"[DocumentSummarizer] Authors: {len(metadata.get('authors', []))} found")
        
        return metadata

    def log_error(self, stage: str, error: str):
        """Enhanced error logging"""
        print(f"[DocumentSummarizer] ERROR in {stage}: {error}")
