# # src/research_assistant/services/reference_extractor.py

# from typing import Dict, List, Any
# import re
# import json
# from openai import OpenAI
# from django.conf import settings
# from pydantic import BaseModel, Field
# import httpx

# class ReferenceEntry(BaseModel):
#     """Schema for an individual reference entry"""
#     ref_id: str = Field(..., description="Reference identifier (e.g., '1' or 'Smith2020')")
#     text: str = Field(..., description="Full reference text")
#     type: str = Field(..., description="Reference type (numbered_bracket, numbered_dot, author_year, etc.)")

# class ReferenceList(BaseModel):
#     """Schema for a complete reference list"""
#     entries: List[ReferenceEntry] = Field(..., description="List of reference entries")

# class ReferenceExtractor:
#     """Extract structured references from pasted reference lists"""
    
#     def __init__(self):
#         print("[ReferenceExtractor] Initializing reference extractor")
#         import importlib.metadata
#         version = importlib.metadata.version("openai")
#         major_version = int(version.split('.')[0])
#         print(f"[DocumentSummarizer] Detected OpenAI version: {version}")
        
#         # Initialize with proxy handling for Railway
#         try:
#             # Standard initialization that fails with 'proxies' parameter in Railway
#             self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
#             self.api_version = "new"
#             print(f"[DocumentSummarizer] Using new OpenAI API v{major_version}.x")
#         except TypeError as e:
#             # Specifically handle the proxies error in Railway
#             if 'proxies' in str(e):
#                 print("[DocumentSummarizer] Detected proxy configuration, using alternate initialization")
                
#                 # Create a custom HTTP client without proxies
#                 http_client = httpx.Client(timeout=120)
#                 self.llm = OpenAI(
#                     api_key=settings.OPENAI_API_KEY,
#                     http_client=http_client  # Use custom client without proxies
#                 )
#                 self.api_version = "new"
#             else:
#                 raise
                
#             print("[DocumentSummarizer] OpenAI client initialized successfully")
#         except Exception as e:
#             print(f"[DocumentSummarizer] CRITICAL ERROR initializing OpenAI client: {str(e)}")
#             self.llm = None
#             self.api_version = None
#             self.init_error = str(e)
    
#     def _construct_prompt(self, reference_text: str) -> str:
#         """Construct prompt for reference extraction"""
#         prompt = f"""
#         # Task: Extract and structure academic references
        
#         Below is a list of academic references. Please extract each reference and identify its format.
        
#         ## Reference List:
#         {reference_text}
        
#         ## Instructions:
#         1. Identify each distinct reference entry
#         2. Determine the reference format/type:
#            - 'numbered_bracket' for references like "[1] Author. Title..."
#            - 'numbered_dot' for references like "1. Author. Title..."
#            - 'author_year' for references like "[Author(2023)] Title..."
#            - 'parenthetical' for references like "(Smith, 2020) Title..."
#            - 'narrative' for references like "Author et al.(2016) Title..."
#            - 'standard' for references like "Smith, J. (2020). Title..."
#         3. For each reference, extract:
#            - ref_id: The identifier (number or author+year)
#            - text: The complete reference text
#            - type: The reference format type
        
#         Return the structured references as a JSON object.
#         Make sure every reference has a unique ref_id.
#         If there's no explicit numbering, create IDs like "ref1", "ref2", etc.
        
#         ## Output Format:
#         {{
#             "entries": [
#                 {{
#                     "ref_id": "1",
#                     "text": "Full reference text here...",
#                     "type": "numbered_bracket"
#                 }},
#                 ...more entries...
#             ]
#         }}
#         """
#         return prompt
    
#     def _preprocess_reference_text(self, text: str) -> str:
#         """Clean and normalize reference text"""
#         # Remove excessive whitespace
#         text = re.sub(r'\s+', ' ', text)
#         # Split on likely reference boundaries but preserve the content
#         lines = re.split(r'(?=\[\d+\]|\d+\.|^\[?[A-Z][a-z]+,)', text)
#         # Clean up each line
#         lines = [line.strip() for line in lines if line.strip()]
#         # Rejoin with clear separation
#         return '\n'.join(lines)
    
#     def extract_references(self, reference_text: str) -> Dict[str, Any]:
#         """Extract structured references from pasted text"""
        
#         print("Strat Extract structured references")
#         if not reference_text or not self.llm:
#             return {'entries': {}}
        
#         # Preprocess the reference text
#         cleaned_text = self._preprocess_reference_text(reference_text)
        
#         try:
#             print("Start OpenAI reference extraction... ")
#             if self.api_version == "new":
#                 print("Using new OpenAI API style")
#                 response = self.llm.chat.completions.create(
#                     model="gpt-4o-mini",
#                     messages=[{
#                         "role": "system",
#                         "content": self._construct_prompt(cleaned_text)
#                     }],
#                     temperature=0.9,
#                 )
#             else:
#                 print("Using old OpenAI API style")
#                 http_client = httpx.Client(timeout=120)
#                 client = OpenAI(api_key=settings.OPENAI_API_KEY, http_client=http_client)
#                 response = client.chat.completions.create(
#                     model="gpt-3.5-turbo-0613",
#                     messages=[{
#                         "role": "system",
#                         "content": self._construct_prompt(cleaned_text)
#                     }],
#                     temperature=0.9,
#                 )

#             print("Reference extraction complete")
            
#             # Extract response text and convert to JSON
#             content = response.choices[0].message.content  # Extract response text
#             reference_data = json.loads(content)  # Convert JSON string to dictionary
            
#             print("Reference content:", reference_data)

#             # Convert list format to dictionary format
#             structured_references = {
#                 'entries': {},
#                 'type': 'manual',
#                 'start_page': None,
#                 'end_page': None
#             }

#             # Process each entry
#             for entry in reference_data.get('entries', []):
#                 ref_id = entry.get('ref_id')
#                 if ref_id:
#                     structured_references['entries'][ref_id] = {
#                         'text': entry.get('text', ''),
#                         'type': entry.get('type', 'standard')
#                     }

#             print("Return reference data")
#             return structured_references

#         except Exception as e:
#             print(f"[ReferenceExtractor] Error extracting references: {str(e)}")
#             return {'entries': {}}





# src/research_assistant/services/reference_extractor.py
from typing import Dict, List, Any
import re
import json
from openai import OpenAI
from django.conf import settings
from pydantic import BaseModel, Field
import httpx
import time
import logging


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
        try:
            print("[ReferenceExtractor] Initializing OpenAI client...")
            print(f"[ReferenceExtractor] API Key Set: {bool(settings.OPENAI_API_KEY)}")
            print(f"[ReferenceExtractor] API Key Length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")
            
            # Import to check version
            import importlib.metadata
            version = importlib.metadata.version("openai")
            major_version = int(version.split('.')[0])
            print(f"[ReferenceExtractor] Detected OpenAI version: {version}")
            
            # Initialize with proxy handling for Railway
            try:
                # Standard initialization that fails with 'proxies' parameter in Railway
                self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.api_version = "new"
                print(f"[ReferenceExtractor] Using new OpenAI API v{major_version}.x")
            except TypeError as e:
                # Specifically handle the proxies error in Railway
                if 'proxies' in str(e):
                    print("[ReferenceExtractor] Detected proxy configuration, using alternate initialization")
                    import httpx
                    # Create a custom HTTP client without proxies
                    http_client = httpx.Client(timeout=180)  # Extended timeout of 3 minutes
                    self.llm = OpenAI(
                        api_key=settings.OPENAI_API_KEY,
                        http_client=http_client  # Use custom client without proxies
                    )
                    self.api_version = "new"
                else:
                    raise
                    
            print("[ReferenceExtractor] OpenAI client initialized successfully")
        except Exception as e:
            print(f"[ReferenceExtractor] CRITICAL ERROR initializing OpenAI client: {str(e)}")
            self.llm = None
            self.api_version = None
            self.init_error = str(e)

    def _construct_prompt(self, reference_text: str) -> str:
        """Construct prompt for reference extraction"""
        prompt = f"""
        # Task: Extract and structure academic references \n
        
        Below is a list of academic references. Please extract each reference and identify its format, the list is mostlikely unstructured,and spaced incorrectly.
        With your understanding of what a single reference looks like please extract each reference in full the extact wording. \n
        
        ## Reference List:
        {reference_text} \n \n
        
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
        - text: The complete reference text
        - type: The reference format type
        
        Return the structured references as a JSON object.
        Make sure every reference has a unique ref_id.
        If there's no explicit numbering, create IDs like "1", "2", etc. \n \n

        IMPORTANT: The reference list could be a mess it your job to discern what is the full reference, when it starts and when it ends. KEY TIP nearly all reference start with the authors.  
        Each reference list is different You must recognise the patterns to discern what the start and when it ends to extract the reference correctly. 
        
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

    def _split_reference_list(self, text: str, max_chunk_size: int = 8000) -> List[str]:
        """Split long reference list into manageable chunks"""
        # Initial clean
        cleaned_text = self._preprocess_reference_text(text)
        
        # Split by common reference patterns
        pattern = r'(?=\[\d+\]|\d+\.|^\[?[A-Z][a-z]+,|\(\d{4}\))'
        references = re.split(pattern, cleaned_text)
        references = [ref.strip() for ref in references if ref.strip()]
        
        chunks = []
        current_chunk = ""
        
        for ref in references:
            if len(current_chunk) + len(ref) > max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = ref
            else:
                current_chunk += "\n" + ref if current_chunk else ref
        
        if current_chunk:
            chunks.append(current_chunk)
        
        print(f"[ReferenceExtractor] Split reference list into {len(chunks)} chunks")
        return chunks

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
        
        print("Starting reference extraction")
        print("[ReferenceExtractor] Starting reference extraction")
        
        if not reference_text or not self.llm:
            return {'entries': {}}
        
        # Split long texts into chunks
        chunks = self._split_reference_list(reference_text)
        
        # Process each chunk and combine results
        all_entries = []
        ref_id_counter = 1
        
        for i, chunk in enumerate(chunks):
            print(f"[ReferenceExtractor] Processing chunk {i+1}/{len(chunks)}")
            
            # Maximum retry attempts
            max_retries = 3
            retry_delay = 5  # seconds
            
            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    
                    # Choose API call style based on detected version
                    if self.api_version == "new":
                        print("[ReferenceExtractor] Using new OpenAI API style")
                        
                        # Create fresh client with timeout for reliability
                        http_client = httpx.Client(timeout=180)  # 3 minutes
                        client = OpenAI(
                            api_key=settings.OPENAI_API_KEY,
                            http_client=http_client
                        )
                        
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo-0125",  # Use a stable model for parsing
                            messages=[{
                                "role": "system",
                                "content": self._construct_prompt(chunk)
                            }],
                            temperature=0.2  # Lower temperature for consistency
                        )
                        content = response.choices[0].message.content
                    else:
                        print("[ReferenceExtractor] Using old OpenAI API style")
                        http_client = httpx.Client(timeout=180)
                        
                        # Old API style uses different parameters
                        client = OpenAI(api_key=settings.OPENAI_API_KEY, http_client=http_client)
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo-0613",
                            messages=[{
                                "role": "system",
                                "content": self._construct_prompt(chunk)
                            }],
                            temperature=0.2
                        )
                        content = response.choices[0].message.content
                    
                    duration = time.time() - start_time
                    print(f"OpenAI response received in {duration:.2f}s")
                    print(f"[ReferenceExtractor] OpenAI response received in {duration:.2f}s")
                    
                    # Parse the JSON response
                    reference_data = json.loads(content)
                    
                    # Add entries from this chunk
                    entries = reference_data.get('entries', [])
                    
                    # Check for duplicate IDs
                    existing_ids = {e.get('ref_id') for e in all_entries}
                    
                    for entry in entries:
                        ref_id = entry.get('ref_id')
                        if ref_id in existing_ids:
                            # Generate a new unique ID
                            while f"ref{ref_id_counter}" in existing_ids:
                                ref_id_counter += 1
                            entry['ref_id'] = f"{ref_id_counter}"
                            ref_id_counter += 1
                        
                        all_entries.append(entry)
                    
                    # Break the retry loop on success
                    break
                    
                except Exception as e:
                    print(f"Error during API call (attempt {attempt+1}/{max_retries}): {str(e)}")
                    print(f"[ReferenceExtractor] Error during API call: {str(e)}")
                    
                    if attempt < max_retries - 1:
                        print(f"[ReferenceExtractor] Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        print("[ReferenceExtractor] Max retries reached for this chunk")
        
        # Convert to the expected dictionary structure
        structured_references = {
            'entries': {},
            'type': 'manual',
            'start_page': None,
            'end_page': None
        }
        
        # Process all entries
        for entry in all_entries:
            ref_id = entry.get('ref_id')
            if ref_id:
                structured_references['entries'][ref_id] = {
                    'text': entry.get('text', ''),
                    'type': entry.get('type', 'standard')
                }
        
        print(f"[ReferenceExtractor] Extracted {len(structured_references['entries'])} references")
        return structured_references
