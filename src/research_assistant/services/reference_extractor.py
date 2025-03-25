# src/research_assistant/services/reference_extractor.py

from typing import Dict, List, Any
import re
import json
from openai import OpenAI
from django.conf import settings
from pydantic import BaseModel, Field

class ReferenceEntry(BaseModel):
    """Schema for an individual reference entry"""
    ref_id: str = Field(..., description="Reference identifier (e.g., '1' or 'Smith2020')")
    text: str = Field(..., description="Full reference text")
    type: str = Field(..., description="Reference type (numbered_bracket, numbered_dot, author_year, etc.)")

class ReferenceList(BaseModel):
    """Schema for a complete reference list"""
    entries: List[ReferenceEntry] = Field(..., description="List of reference entries")

class ReferenceExtractor:
    """Extract structured references from pasted reference lists"""
    
    def __init__(self):
        print("[ReferenceExtractor] Initializing reference extractor")
        try:
            self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
            print("[ReferenceExtractor] OpenAI client initialized successfully")
        except Exception as e:
            print(f"[ReferenceExtractor] Error initializing OpenAI client: {str(e)}")
            self.llm = None
    
    def _construct_prompt(self, reference_text: str) -> str:
        """Construct prompt for reference extraction"""
        prompt = f"""
        # Task: Extract and structure academic references
        
        Below is a list of academic references. Please extract each reference and identify its format.
        
        ## Reference List:
        {reference_text}
        
        ## Instructions:
        1. Identify each distinct reference entry
        2. Determine the reference format/type:
           - 'numbered_bracket' for references like "[1] Author. Title..."
           - 'numbered_dot' for references like "1. Author. Title..."
           - 'author_year' for references like "[Author(2023)] Title..."
           - 'parenthetical' for references like "(Smith, 2020) Title..."
           - 'narrative' for references like "Author et al.(2016) Title..."
           - 'standard' for references like "Smith, J. (2020). Title..."
        3. For each reference, extract:
           - ref_id: The identifier (number or author+year)
           - text: The complete reference text
           - type: The reference format type
        
        Return the structured references as a JSON object.
        Make sure every reference has a unique ref_id.
        If there's no explicit numbering, create IDs like "ref1", "ref2", etc.
        
        ## Output Format:
        {{
            "entries": [
                {{
                    "ref_id": "1",
                    "text": "Full reference text here...",
                    "type": "numbered_bracket"
                }},
                ...more entries...
            ]
        }}
        """
        return prompt
    
    def _preprocess_reference_text(self, text: str) -> str:
        """Clean and normalize reference text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Split on likely reference boundaries but preserve the content
        lines = re.split(r'(?=\[\d+\]|\d+\.|^\[?[A-Z][a-z]+,)', text)
        # Clean up each line
        lines = [line.strip() for line in lines if line.strip()]
        # Rejoin with clear separation
        return '\n'.join(lines)
    
    def extract_references(self, reference_text: str) -> Dict[str, Any]:
        """Extract structured references from pasted text"""
        
        print("Strat Extract structured references")
        if not reference_text or not self.llm:
            return {'entries': {}}
        
        # Preprocess the reference text
        cleaned_text = self._preprocess_reference_text(reference_text)
        
        try:
            print("Start Openai reference extraction... ")
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": self._construct_prompt(cleaned_text)
                }],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            print("reference extraction complete")
            # Parse the response
            content = response.choices[0].message.content
            reference_data = json.loads(content)
            
            
            # Convert list format to dictionary format to match existing structure
            structured_references = {
                'entries': {},
                'type': 'manual',
                'start_page': None,
                'end_page': None
            }
            print("struture reference data ")
            # Process each entry
            for entry in reference_data.get('entries', []):
                ref_id = entry.get('ref_id')
                if ref_id:
                    structured_references['entries'][ref_id] = {
                        'text': entry.get('text', ''),
                        'type': entry.get('type', 'standard')
                    }
            print("return reference data")
            return structured_references
            
        except Exception as e:
            print(f"[ReferenceExtractor] Error extracting references: {str(e)}")
            return {'entries': {}}