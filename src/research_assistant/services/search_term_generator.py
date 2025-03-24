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
            self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
            print("[SearchTermGenerator] OpenAI client initialized successfully")
        except Exception as e:
            print(f"[SearchTermGenerator] CRITICAL ERROR initializing OpenAI client: {str(e)}")
            self.llm = None
            self._init_error = str(e)
    
    def _construct_prompt(self, context: str) -> str:
        """Construct prompt for generating search terms"""
        prompt = f"""
        # Research Context\n
        {context} \n \n

        ## Task\n
        Analyze the research context above and identify key themes for academic literature searches.
        Generate 6 distinct categories of search terms with 4 search queries each (24 total search terms).
        \n
        For each category:
        1. Provide a descriptive category name
        2. Include a brief description of what this category aims to find
        3. Generate 3 specific search queries tailored for arXiv academic search
        
        Make search terms specific enough to return relevant results but not too narrow.
        Follow academic search conventions (e.g., "machine learning classification algorithms").
        
        ## Response Format
        Return a JSON object with categories, descriptions, and search terms as specified in the SearchTermsResponse schema.
        """
        return prompt
    
    def generate_search_terms(self, context: str) -> Dict[str, Any]:
        """Generate search terms from research context"""
        print("[SearchTermGenerator] Generating search terms from context")

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
            
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": self._construct_prompt(context)
                }],
                temperature=0.7,
                functions=[function_schema],
                function_call={"name": "generate_search_terms"}
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