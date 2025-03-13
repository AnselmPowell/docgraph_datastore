# src/research_assistant/services/document_summarizer.py
from typing import Dict
from openai import OpenAI, APIError, RateLimitError, APITimeoutError
from django.conf import settings
import json
import time
import logging
import traceback
from pydantic import BaseModel, Field
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class MetadataSchema(BaseModel): 
    """Schema for document metadata extraction"""
    title: str = Field(..., description="Document title")
    authors: list[str] = Field(..., description="List of authors")
    publication_date: str = Field(None, description="Publication date if available")
    publisher: str = Field(None, description="Publisher name if available") 
    doi: str = Field(None, description="DOI if available")
    citation: str = Field(..., description="Full Harvard citation/reference of this paper/book in aacademic format")
    reference: str = Field(..., description="Full reference entry")
    summary: str = Field(..., description="2-3 sentence summary")
    total_pages: int = Field(default=1, description="Total number of pages")

class DocumentSummarizer:
    """Generate document summary and extract metadata"""
    
    # def __init__(self):
    #     try:
    #         print("[DocumentSummarizer] Initializing OpenAI client...")
    #         print(f"[DocumentSummarizer] API Key Set: {bool(settings.OPENAI_API_KEY)}")
    #         print(f"[DocumentSummarizer] API Key Length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")
    #         self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
    #         print("[DocumentSummarizer] OpenAI client initialized successfully")
    #     except Exception as e:
    #         print(f"[DocumentSummarizer] CRITICAL ERROR initializing OpenAI client: {str(e)}")
    #         logger.error(f"OpenAI initialization error: {str(e)}")
    #         logger.error(traceback.format_exc())
    #         # Continue without crashing, we'll handle it in generate_summary
    #         self.llm = None
    #         self.init_error = str(e)

    def __init__(self):
        try:
            print("[DocumentSummarizer] Initializing OpenAI client...")
            print(f"[DocumentSummarizer] API Key Set: {bool(settings.OPENAI_API_KEY)}")
            print(f"[DocumentSummarizer] API Key Length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")
            
            # Version-compatible initialization
            try:
                # Try the newer initialization method first
                self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.api_version = "new"
                print("[DocumentSummarizer] Using new OpenAI API v1.x")
            except TypeError as e:
                if 'proxies' in str(e):
                    # Handle older OpenAI library versions
                    import openai
                    openai.api_key = settings.OPENAI_API_KEY
                    self.llm = openai
                    self.api_version = "old"
                    print("[DocumentSummarizer] Using older OpenAI API v0.x")
                else:
                    raise
                    
            print("[DocumentSummarizer] OpenAI client initialized successfully")
        except Exception as e:
            print(f"[DocumentSummarizer] CRITICAL ERROR initializing OpenAI client: {str(e)}")
            self.llm = None
            self.api_version = None
            self.init_error = str(e)


    def _construct_prompt(self, pages_text: list[str]) -> str:
        """Construct metadata extraction prompt using first two pages
        
        Input:
            pages_text: list[str] - List of first two pages text content
            
        Output:
            str - Constructed prompt for LLM
        """

        
        # Combine first two pages with separator
        combined_text = "\n---PAGE BREAK---\n".join(pages_text)

        
        prompt = f"""
        Academic Document Text (First Two Pages):
        {combined_text}

        \n#####

        Above is the text from the first two pages of an academic document. Please analyze this text and extract key metadata.
        Focus on identifying:
        1. Title (required)
        2. Authors (required)
        3. Publication date (if available, format: YYYY-MM-DD)
        4. Publisher (if available)
        5. DOI (if available)
        6. Generate proper academic citation (required)
        7. Create full reference entry (required) HARVARD REFERENCE FORMAT
        8. Write 2-3 sentence summary of main topic/findings (required)
        9. Total pages (default to 1 if not found)
        
        Extract ALL available information but leave optional fields empty if not found.
        Ensure citation and reference follow academic format standards.
        For missing dates, use logical inference from content or citations if possible.

        Respond in JSON format matching the MetadataSchema.
        """

        return prompt

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""

        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def _parse_date(self, date_str: str) -> str:
        """Parse and validate publication date"""
        if not date_str:

            return None
            

        
        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%Y'):
            if parsed_date := self._try_parse_date(date_str, fmt):

                return parsed_date
        

        return None

    def _try_parse_date(self, date_str: str, fmt: str) -> str:
        """Helper function to try parsing a date with a specific format"""
        try:
            if isinstance(date_str, str):

                parsed_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')

                return parsed_date
        except Exception as e:

            return None

    def generate_summary(self, document_sections: list[Dict], document_id: str) -> Dict:
        """Generate document summary with proper API version handling"""
        logger.info(f"Starting document summary generation for document: {document_id}")
        print(f"Starting summary generation, API version: {self.api_version}")
        # Fallback metadata if OpenAI fails
        # fallback_metadata = {
        #     'title': "Document " + document_id,
        #     'authors': ['Unknown Author'],
        #     'publication_date': None,
        #     'publisher': None,
        #     'doi': None,
        #     'citation': f"Unknown (). Document ID: {document_id}",
        #     'reference': f"Unknown (). Document ID: {document_id}",
        #     'summary': "This document could not be automatically summarized.",
        #     'total_pages': len(document_sections)
        # }
        
        print(" Is Self LLM")
        if self.llm is None:
            print(f"[DocumentSummarizer] Using fallback due to initialization error: {getattr(self, 'init_error', 'Unknown error')}")
            # return fallback_metadata
        
        # Get text from first two pages
        first_two_pages = []
        for section in document_sections[:2]:
            if section['content']['text']:
                cleaned_text = self._clean_text(section['content']['text'])
                first_two_pages.append(cleaned_text)
        
        if not first_two_pages:
            logger.warning(f"No page content available for document: {document_id}")
            # return fallback_metadata
        
        # Create function schema for LLM
        function_schema = {
            "name": "extract_document_metadata",
            "parameters": MetadataSchema.schema()
        }
        
        logger.info("Calling OpenAI API for metadata extraction...")
        print(f"Calling OpenAI API with version {self.api_version}...")
        
        # Maximum retry attempts
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # Choose API call style based on detected version
                if self.api_version == "new":
                    print("Using new OpenAI API style")
                    response = self.llm.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{
                            "role": "system",
                            "content": self._construct_prompt(first_two_pages)
                        }],
                        temperature=0.3,
                        functions=[function_schema],
                        function_call={"name": "extract_document_metadata"}
                    )
                    metadata = json.loads(response.choices[0].message.function_call.arguments)
                else:
                    print("Using old OpenAI API style")
                    # Old API style uses different parameters and response format
                    response = self.llm.ChatCompletion.create(
                        model="gpt-3.5-turbo-0613",  # Old API model that supports function calling
                        messages=[{
                            "role": "system",
                            "content": self._construct_prompt(first_two_pages)
                        }],
                        temperature=0.3,
                        functions=[function_schema],
                        function_call={"name": "extract_document_metadata"}
                    )
                    metadata = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
                
                duration = time.time() - start_time
                logger.info(f"OpenAI response received in {duration:.2f}s")
                print(f"OpenAI response received in {duration:.2f}s")
                
                # Process publication date if present
                if metadata.get('publication_date'):
                    metadata['publication_date'] = self._parse_date(metadata['publication_date'])
                
                logger.info(f"Metadata extraction complete: {list(metadata.keys())}")
                print("OpenAI summary complete!")
                return metadata

            except Exception as e:
                logger.error(f"Error during API call (attempt {attempt+1}/{max_retries}): {str(e)}", exc_info=True)
                print(f"Error during API call: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max retries reached, using fallback metadata")
                    # return fallback_metadata