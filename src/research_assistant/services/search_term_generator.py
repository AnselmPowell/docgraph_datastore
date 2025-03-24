# src/research_assistant/services/search_term_generator.py
from typing import List, Dict, Any
from openai import OpenAI
from django.conf import settings
import json
import time
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class SearchCategorySchema(BaseModel):
    """Schema for search categories and terms"""
    category: str = Field(..., description="Category name for the search terms")
    description: str = Field(..., description="Brief description of what this category aims to find")
    search_terms: List[str] = Field(..., description="List of search terms/queries related to this category")

class SearchTermsResponse(BaseModel):
    """Schema for the complete search terms response"""
    categories: List[SearchCategorySchema] = Field(..., description="List of search categories with terms")

class SearchTermGenerator:
    """Generate search terms from research context using OpenAI"""
    
    def __init__(self):
        print("[SearchTermGenerator] Initializing")
        try:
                print("[DocumentSummarizer] Initializing OpenAI client...")
                print(f"[DocumentSummarizer] API Key Set: {bool(settings.OPENAI_API_KEY)}")
                print(f"[DocumentSummarizer] API Key Length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")
                
                # Import to check version
                import openai
                import importlib.metadata
                version = importlib.metadata.version("openai")
                major_version = int(version.split('.')[0])
                print(f"[DocumentSummarizer] Detected OpenAI version: {version}")
                
                # Initialize with proxy handling for Railway
                try:
                    # Standard initialization that fails with 'proxies' parameter in Railway
                    self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
                    self.api_version = "new"
                    print(f"[DocumentSummarizer] Using new OpenAI API v{major_version}.x")
                except TypeError as e:
                    # Specifically handle the proxies error in Railway
                    if 'proxies' in str(e):
                        print("[DocumentSummarizer] Detected proxy configuration, using alternate initialization")
                        import httpx
                        # Create a custom HTTP client without proxies
                        http_client = httpx.Client(timeout=120)
                        self.llm = OpenAI(
                            api_key=settings.OPENAI_API_KEY,
                            http_client=http_client  # Use custom client without proxies
                        )
                        self.api_version = "new"
                    else:
                        raise
                        
                print("[DocumentSummarizer] OpenAI client initialized successfully")
        except Exception as e:
            print(f"[DocumentSummarizer] CRITICAL ERROR initializing OpenAI client: {str(e)}")
            self.llm = None
            self.api_version = None
            self.init_error = str(e)
    
    def _construct_prompt(self, context: str) -> str:
        """Construct prompt for generating search terms"""
        prompt = f"""
        # Research Context\n
        {context} \n \n

        ## Task\n
        Analyse the research context above and identify key themes for academic literature searches, It needs to cover all relevant and significant research related to the main context topics .
        You need to Center your search queries around the main themes and concepts of the context provided.
        Generate between 4 to 10 distinct categories of search terms with 4 search queries each (24 total search terms).
        \n
        For each category (min 4 - max 10) :
        1. Provide a descriptive category name
        2. Include a brief description of what this category aims to find
        3. Generate 4 specific search queries tailored towards the contexts to get the most relevant results
    
        Make search terms specific enough to return relevant results but not too narrow, focus on all the main aspect of the research contexxt.
        Follow academic search conventions (e.g., "machine learning classification algorithms").
        
        ## Response Format
        Return a JSON object with categories, descriptions, and search terms as specified in the SearchTermsResponse schema.
        """
        return prompt
    
    def generate_search_terms(self, context: str) -> Dict[str, Any]:
        """Generate search terms from research context"""
        print("[SearchTermGenerator] Generating search terms from context")
        print(f"Starting search query generation, API version: {self.api_version}")

        print('context:', context)
        
        if self.llm is None:
            print(f"[SearchTermGenerator] Cannot generate search terms: OpenAI client initialization failed: {getattr(self, '_init_error', 'Unknown error')}")
            return {
                "categories": [
                    {
                        "category": "General Research",
                        "description": "Could not generate search terms - OpenAI client unavailable",
                        "search_terms": ["research papers", "academic literature"]
                    }
                ]
            }
        
        function_schema = {
            "name": "generate_search_terms",
            "parameters": SearchTermsResponse.schema()
        }
        
        try:
            start_time = time.time()
            if self.api_version == "new":
                    print("Using new OpenAI API style")
                    response = self.llm.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{
                            "role": "system",
                            "content": self._construct_prompt(context)
                        }],
                        temperature=0.9,
                        functions=[function_schema],
                        function_call={"name": "generate_search_terms"}
                    )
            else:
                print("Using old OpenAI API style")
                # Old API style uses different parameters and response format
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo-0613",
                    messages=[{
                        "role": "system",
                        "content": self._construct_prompt(first_two_pages)
                    }],
                    temperature=0.7,
                    functions=[function_schema],
                    function_call={"name": "extract_document_metadata"}
                )

            duration = time.time() - start_time
            print(f"[SearchTermGenerator] Generated search terms in {duration:.2f}s")
            
            search_terms = json.loads(response.choices[0].message.function_call.arguments)
            
            print(f"[SearchTermGenerator] Generated {len(search_terms['categories'])} categories with search terms")
            return search_terms
            
        except Exception as e:
            print(f"[SearchTermGenerator] Error generating search terms: {str(e)}")
            logger.error(f"Error generating search terms: {str(e)}", exc_info=True)
            
            # Fallback response
            return {
                "categories": [
                    {
                        "category": "Error",
                        "description": f"Failed to generate search terms: {str(e)}",
                        "search_terms": ["research papers", "academic literature"]
                    }
                ]
            }