# src/research_assistant/services/document_searcher.py
from typing import Dict, List
import json
from openai import OpenAI
from django.conf import settings
from pydantic import BaseModel, Field
from .monitoring.system_monitor import AIModelCosts
from .cache_manager import DocumentCacheManager

class SearchResultSchema(BaseModel):
    """Schema for section search results"""
    has_context: bool = Field(..., description="Whether section contains context")
    context: str = Field(None, description="Matching context text")
    has_theme: bool = Field(..., description="Whether section contains theme")
    theme: str = Field(None, description="Matching theme text") 
    has_keyword: bool = Field(..., description="Whether section contains keyword")
    keyword: str = Field(None, description="Matching keyword text")
    has_similar_keyword: bool = Field(..., description="Whether section contains similar keyword")
    similar_keyword: str = Field(None, description="Matching similar keyword text")
    section_type: str = Field("text", description="Type of section (text, table, figure, etc)")

class DocumentSearcher:
    """Search document sections for relevant content with enhanced monitoring"""
    
    def __init__(self):
        print("\n[DocumentSearcher] Initializing searcher")

        self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.total_tokens_used = 0
        self.total_api_calls = 0
        print("[DocumentSearcher] Initialization complete")
        self.cache_manager = DocumentCacheManager()

    def _construct_search_prompt(
        self,
        text: str,
        context: str,
        theme: str,
        keywords: List[str],
        summary: str,
    ) -> str:
        """Construct section analysis prompt with context awareness"""
        print("\n[DocumentSearcher] Constructing search prompt")
        
        # Validate and sanitize inputs
        text = str(text) if text is not None else ''
        context = str(context) if context is not None else ''
        theme = str(theme) if theme is not None else ''
        summary = str(summary) if summary is not None else ''
        keywords_str = ', '.join(str(k) for k in keywords) if keywords else ''
        
        print(f"[DocumentSearcher] Text length: {len(text)}")
        print(f"[DocumentSearcher] Context: {context}")
        print(f"[DocumentSearcher] Theme: {theme}")
        print(f"[DocumentSearcher] Keywords: {keywords_str}")
        
        # Your original prompt with proper formatting
        prompt = f"""
        Background Academic Document Summary: \n
        {summary} \n

        Above is a summary of a academic document to understand the what the academic document is about. \n
        The user is looking for specific infomration in the document. below is thier search criteria. \n
        Context is the information the user is looking for in the document. \n
        Theme is the topic or subject matter of the document the user provided. \n
        Keywords are the exact keywords that the user is looking for in the document. \n
        Similar keywords are synonyms or related concepts to the keywords that are in the document based on the context.\n \n

        Search Criteria: \n
        # Context: \n
        {context} \n
        # Theme: \n
        {theme} \n
        # Keywords: \n
        {keywords_str} \n \n ####


        # Your goal is to use the Search Criterias above given by the user to analyze the Document Section Content below and determine if any of it is relevant to the user based on the search criteria. \n

        # Current Document Section Content Below: \n
        {text} \n \n####

        Note: The Document Section Content Above is one part of the Academic Document, Focus your analysis only on the "Current Section" above 
        
        ## Your goal is to use the Search Criterias to analyze the Current Section and determine if it is relevant to the user's search. \n
        Any uncertainty should be marked as false. \n

        Task: Analyze the current section against the search criteria:
        1. Context Match: Does the section directly relate to the context? If yes, extract the exact matching text from the section. \n
        2. Theme Match: Does the section align with the theme? If yes, extract the exact matching text.
        3. Keyword Match: Does the section contain any exact keywords? If yes, extract the sentence containing the keyword from the section. \n
        4. Similar Concepts: Does the section contain related concepts? If yes, extract the relevant text.

        Strict Matching Rules:
        - Only mark as true if there is a clear, direct match in the current section if not return false
        - Use context to understand meaning but extract matches only from current section
        - Default to false if uncertain
        - Context matches must be topically relevant, it can argue for or against the context, if uncertain return false
        - Theme matches must show clear thematic alignment 
        """
        
        print(f"[DocumentSearcher] Prompt constructed, length: {len(prompt)}")
        return prompt

    def analyze_section(
        self,
        section: Dict,  # Now takes full section data instead of just text
        context: str,
        theme: str,
        keywords: List[str],
        summary: str,
    ) -> Dict:
        """Analyze section with context awareness"""
        print("\n[DocumentSearcher] Starting section analysis")
        

        # Get main text and context
        main_text = section['text']
        
        # Build full text with context if available
        analysis_text = []
        
        analysis_text.append(main_text)

        
        # Combine all text
        full_text = "\n".join(analysis_text)
        
        prompt = self._construct_search_prompt(
            full_text, context, theme, keywords, summary
        )
        print(f"[DocumentSearcher] Search prompt: \n {prompt}")

            
        function_schema = {
            "name": "analyze_section_content",
            "parameters": SearchResultSchema.schema()
        }


        print("[DocumentSearcher] Calling OpenAI API")
        response = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": prompt
            }],
            temperature=0.3,
            functions=[function_schema],
            function_call={"name": "analyze_section_content"}
        )
       
        
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        # Track API usage
        self.total_tokens_used += total_tokens
        self.total_api_calls += 1

        print(f"[DocumentSearcher] API call completed, tokens used: {response.usage.total_tokens}")
        print(f"[DocumentSearcher] prompt_tokens", prompt_tokens)
        print(f"[DocumentSearcher] completion_tokens", completion_tokens)
        print(f"[DocumentSearcher] total_tokens", self.total_tokens_used)
        print(f"[DocumentSearcher] estimated_cost", AIModelCosts.calculate_cost(
            total_tokens, 
            "gpt4-mini",
            is_cached=False,
            is_batch=False
        ))
    
        results = json.loads(response.choices[0].message.function_call.arguments)
        print(f"[DocumentSearcher] API response received:" , results)
        print("[DocumentSearcher] Analysis results:")
        print(f"  Context match: {results['has_context']}")
        print(f"  Theme match: {results['has_theme']}")
        print(f"  Keyword match: {results['has_keyword']}")
        print(f"  Similar keyword match: {results['has_similar_keyword']}")

        
        
        return results

    def calculate_relevance_score(
        self,
        total_sections: int,
        context_matches: int,
        theme_matches: int,
        keyword_matches: int,
        similar_matches: int,
        document_relevance: bool
    ) -> float:
        """Calculate relevance score with detailed monitoring"""
        print("\n[DocumentSearcher] Calculating relevance score")

        print(f"[DocumentSearcher] Total sections: {total_sections}")
        print(f"[DocumentSearcher] Context matches: {context_matches}")
        print(f"[DocumentSearcher] Theme matches: {theme_matches}")
        print(f"[DocumentSearcher] Keyword matches: {keyword_matches}")
        print(f"[DocumentSearcher] Similar keyword matches: {similar_matches}")
        
        # Calculate components
        context_score = (context_matches) * 10
        theme_score = (theme_matches) * 4
        keyword_score = (keyword_matches) * 4
        similar_score = (similar_matches) * 1
        summary_bonus = 4 if document_relevance else 0
        
        # Calculate total
        total_score = context_score + theme_score + keyword_score + similar_score + summary_bonus
        final_score = min(total_score, 100.0)
        
        print("[DocumentSearcher] Score components:")
        print(f"  Context score: {context_score:.2f}")
        print(f"  Theme score: {theme_score:.2f}")
        print(f"  Keyword score: {keyword_score:.2f}")
        print(f"  Similar concepts score: {similar_score:.2f}")
        print(f"  Summary bonus: {summary_bonus}")
        print(f"  Final score: {final_score:.2f}")
        
        
        return final_score

    def check_summary_relevance(
        self,
        summary: str,
        context: str
    ) -> bool:
        """Check summary relevance with monitoring"""
        print("\n[DocumentSearcher] Checking summary relevance")
        print(f"[DocumentSearcher] Summary length: {len(summary)}")
        print(f"[DocumentSearcher] Context length: {len(context)}")
        
        prompt = f"""
            Analyze if this academic document summary is relevant to the given context.
            
            Summary: {summary}
            Context: {context}
            
            Return 'true' only if there is a clear topical match between the context
            and the summary. Return 'false' if unclear or no match.
        """
        
        response = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3
        )
        print(f"[DocumentSearcher] API response summary relevance received:" , response)
        # In check_summary_relevance method, update monitoring:
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        # Track API usage
        self.total_tokens_used += total_tokens
        self.total_api_calls += 1

        print(f"[DocumentSearcher] API call completed, tokens used: {response.usage.total_tokens}")
        print(f"[DocumentSearcher] prompt_tokens", prompt_tokens)
        print(f"[DocumentSearcher] completion_tokens", completion_tokens)
        print(f"[DocumentSearcher] total_tokens", self.total_tokens_used)
        print(f"[DocumentSearcher] estimated_cost", AIModelCosts.calculate_cost(
            total_tokens, 
            "gpt4-mini",
            is_cached=False,
            is_batch=False
        ))

        
        is_relevant = response.choices[0].message.content.strip().lower() == "true"
        print(f"[DocumentSearcher] Summary relevance result: {is_relevant}")
        
        return is_relevant

    def search_document(
        self,
        sections: List[Dict],
        context: str,
        theme: str,
        keywords: List[str],
        summary: str,
        document_id: str
    ) -> Dict:
        """Search document with comprehensive context-aware monitoring"""
        print("\n[DocumentSearcher] Starting full document search")
        print(f"[DocumentSearcher] Total sections: {len(sections)}")

        # Check cache first
        query_data = {
            'context': context,
            'theme': theme,
            'keywords': sorted(keywords),
            'type': 'search'
        }
        query_hash = self.cache_manager.generate_query_hash(query_data)
        
        cached_results = self.cache_manager.get_llm_response_sync(  # Note: sync version
            document_id=document_id,
            response_type='search',
            query_hash=query_hash
        )

        print(f"[DocumentSearcher] Is Search Cached ")
        if cached_results:
            print("[DocumentSearcher] Using cached search results: ")
            # print(x)
            return cached_results
        print(f"[DocumentSearcher] No Search Cached Found ")
        
        
        total_sections = len(sections)
        matches = {
            "context": 0,
            "theme": 0,
            "keyword": 0,
            "similar": 0,
            "relevant_sections": [],
            "relevance_score": 0,
            "total_matches": 0
        }

        # Process each section
        print("[DocumentSearcher] Process each section")
        print(f"[DocumentSearcher] Total sections:", sections[0])
        for idx, section in enumerate(sections, 1):
            # Only analyze text sections with LLM
            if section['section_type'] == 'text':
                print(f"\n[DocumentSearcher] Processing text section number {idx}/{total_sections}")
                
                results = self.analyze_section(
                    section=section,  # Pass full section data
                    context=context,
                    theme=theme,
                    keywords=keywords,
                    summary=summary
                )
                print(f"[DocumentSearcher] Results: {results}")
                
                # Track matches
                print(f"[DocumentSearcher] Adding matches to section")
                if results["has_context"]:
                    matches["context"] += 1
                    section["matching_context"] = results["context"]
                    section["relevance_type"].append("context")
                    print(f"[DocumentSearcher] Matched context: {results['context']}")

                if results["has_theme"]:
                    matches["theme"] += 1
                    section["matching_theme"] = results["theme"]
                    section["relevance_type"].append("theme")
                    print(f"[DocumentSearcher] Matched theme: {results['theme']}")
                    
                if results["has_keyword"]:
                    matches["keyword"] += 1
                    section["matching_keywords"].append(results["keyword"])
                    section["relevance_type"].append("keyword")
                    print(f"[DocumentSearcher] Matched keyword: {results['keyword']}")
                    
                if results["has_similar_keyword"]:
                    matches["similar"] += 1
                    section["matching_similar_keywords"].append(results["similar_keyword"]) 
                    section["relevance_type"].append("similar_keyword")
                    print(f"[DocumentSearcher] Matched similar keyword: {results['similar_keyword']}")

                if any([results["has_context"], results["has_theme"], 
                    results["has_keyword"], results["has_similar_keyword"]]):
                    matches["relevant_sections"].append(section)
                    print("[DocumentSearcher], Add relevant section")
            else:
                # For non-text sections, store if they belong to a matching title group
                if any(s['title_group_number'] == section['title_group_number'] 
                    for s in matches["relevant_sections"]):
                    matches["relevant_sections"].append(section)

        print(f"[DocumentSearcher] Calculating document relevance score")
        is_document_relevance = self.check_summary_relevance(summary, context)

        print(f"[DocumentSearcher] Document relevance: {is_document_relevance}")
        final_score = self.calculate_relevance_score(total_sections, matches["context"],matches["theme"],matches["keyword"],matches["similar"],
            is_document_relevance
        )

        print(f"[DocumentSearcher] Number of relevant sections: {len(matches['relevant_sections'])}")
        print(f"[DocumentSearcher] Final relevance score: {final_score}")
        matches["relevance_score"] = final_score

        # Cache results before returning
        self.cache_manager.store_llm_response_sync(  
            document_id=document_id,
            response_type='search',
            query_hash=query_hash,
            response_data=matches
        )


        return matches


