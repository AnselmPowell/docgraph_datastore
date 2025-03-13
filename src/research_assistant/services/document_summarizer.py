# src/research_assistant/services/document_summarizer.py
from typing import Dict
from openai import OpenAI
from django.conf import settings
import json
from pydantic import BaseModel, Field
import re
from datetime import datetime

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
        """Generate document summary and extract metadata from first two pages
        
        Input:
            document_sections: list[Dict] - List of document sections/pages
            document_id: str - Document identifier
            
        Output:
            Dict - Extracted metadata and summary
        """


        
        # Get text from first two pages
        first_two_pages = []
        for section in document_sections[:2]:  # Only process first two sections/pages
            if section['content']['text']:
                cleaned_text = self._clean_text(section['content']['text'])
                first_two_pages.append(cleaned_text)
        

        
        # Create function schema for LLM
        function_schema = {
            "name": "extract_document_metadata",
            "parameters": MetadataSchema.schema()
        }

        print("Call Openai to Summaries...")
        print("Call Openai to Summaries...")
        print("Call Openai to Summaries...")
        print("Call Openai to Summaries...")
        print("Call Openai to Summaries...")
        

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

        print("OpenAI Summary complete")
        print("OpenAI Summary complete")
        print("OpenAI Summary complete")
        print("OpenAI Summary complete")
        print("OpenAI Summary complete")
        print("OpenAI Summary complete")
        print("OpenAI Summary complete")
        print("OpenAI Summary complete")
        print("OpenAI Summary complete")
        print("OpenAI Summary complete")
        print("OpenAI Summary complete")
        print("OpenAI Summary complete")
        
        # Process publication date if present
        if metadata.get('publication_date'):
            metadata['publication_date'] = self._parse_date(metadata['publication_date'])



        
        return metadata