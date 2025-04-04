# src/research_assistant/services/document_searcher.py

import re
from typing import Dict, List, Any, Optional
import json
from openai import OpenAI
from django.conf import settings
from pydantic import BaseModel, Field
# from .monitoring.system_monitor import AIModelCosts
from research_assistant.services.document_processor import DocumentProcessor
from ..models import DocumentMetadata
from .search.relevance_scorer import RelevanceScorer
from .document_processor import DocumentProcessor
from django.utils import timezone

class SearchMatch(BaseModel):
    """Individual search match result"""
    has_context: bool = Field(..., description="Whether section contains or answers the context provided by the user")
    context: Optional[str] = Field(None, description="Matching context text, provide the exact matching text and the whole sentence from the section")
    has_keyword: bool = Field(..., description="Whether section contains keyword true or false")
    has_similar_keyword: bool = Field(..., description="Whether section contains similar keyword, true or false")
    keyword: Optional[str] = Field(None, description="Matching keyword text, extract the exact keyword from the section")
    similar_keyword: Optional[str] = Field(None, description="Matching similar keyword text, extract the similar keyword")
    keyword_context: Optional[str] = Field(None, description="The full sentence containing the keyword or similar keyword")

class SearchResults(BaseModel):
    """Container for multiple search matches"""
    responses: List[SearchMatch] = Field(..., description="List of all matches found in the section")

class DocumentSearcher:
    """Search document sections for relevant content with enhanced monitoring""" 

    # def __init__(self):
    #     print("\n[DocumentSearcher] Initializing searcher")
    #     try:
    #         # Import to check version
    #         import openai
    #         import importlib.metadata
    #         version = importlib.metadata.version("openai")
    #         major_version = int(version.split('.')[0])
    #         print(f"[DocumentSearcher] Detected OpenAI version: {version}")
            
    #         # Initialize with proxy handling for Railway
    #         try:
    #             # Standard initialization that might fail with 'proxies' parameter in Railway
    #             self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
    #             print(f"[DocumentSearcher] Using OpenAI API v{major_version}.x")
    #         except TypeError as e:
    #             # Specifically handle the proxies error in Railway
    #             if 'proxies' in str(e):
    #                 print("[DocumentSearcher] Detected proxy configuration, using alternate initialization")
    #                 import httpx
    #                 # Create a custom HTTP client without proxies
    #                 http_client = httpx.Client(timeout=120)
    #                 self.llm = OpenAI(
    #                     api_key=settings.OPENAI_API_KEY,
    #                     http_client=http_client  # Use custom client without proxies
    #                 )
    #             else:
    #                 raise
                    
    #         print("[DocumentSearcher] OpenAI client initialized successfully")
    #     except Exception as e:
    #         print(f"[DocumentSearcher] CRITICAL ERROR initializing OpenAI client: {str(e)}")
    #         self.llm = None
    #         self._init_error = str(e)
        
    #     self.total_tokens_used = 0
    #     self.total_api_calls = 0
    #     self.relevance_scorer = RelevanceScorer()
    #     print("[DocumentSearcher] Initialization complete")

    def __init__(self):
        print("\n[DocumentSearcher] Initializing searcher")
        try:
            # Import to check version
            import openai
            import importlib.metadata
            version = importlib.metadata.version("openai")
            major_version = int(version.split('.')[0])
            print(f"[DocumentSearcher] Detected OpenAI version: {version}")
            
            # Initialize with proxy handling for Railway
            try:
                # Standard initialization that might fail with 'proxies' parameter in Railway
                self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
                print(f"[DocumentSearcher] Using OpenAI API v{major_version}.x")
            except TypeError as e:
                # Specifically handle the proxies error in Railway
                if 'proxies' in str(e):
                    print("[DocumentSearcher] Detected proxy configuration, using alternate initialization")
                    import httpx
                    # Create a custom HTTP client without proxies
                    http_client = httpx.Client(timeout=120)
                    self.llm = OpenAI(
                        api_key=settings.OPENAI_API_KEY,
                        http_client=http_client  # Use custom client without proxies
                    )
                else:
                    raise
                    
            print("[DocumentSearcher] OpenAI client initialized successfully")
        except Exception as e:
            print(f"[DocumentSearcher] CRITICAL ERROR initializing OpenAI client: {str(e)}")
            self.llm = None
            self._init_error = str(e)
        
        self.total_tokens_used = 0
        self.total_api_calls = 0
        self.api_usage_records = []  # Add this to track usage
        self.relevance_scorer = RelevanceScorer()
        print("[DocumentSearcher] Initialization complete")

    def _construct_search_prompt(
        self,
        text: str,
        context: str,
        keywords: List[str],
        summary: str,
    ) -> str:
        """Construct section analysis prompt with context awareness"""
        print("\n[DocumentSearcher] Constructing search prompt")
        
        # Validate and sanitize inputs
        text = str(text) if text is not None else ''
        context = str(context) if context is not None else ''
        summary = str(summary) if summary is not None else ''
        keywords_str = ', '.join(str(k) for k in keywords) if keywords else ''
        
        print(f"[DocumentSearcher] Text length: {len(text)}")
        print(f"[DocumentSearcher] Context: {context}")
        print(f"[DocumentSearcher] Keywords: {keywords_str}")
        
        # Your original prompt with proper formatting
        prompt = f"""
        # BACKGROUND 
        # Background of the Academic Document Summary: \n
        {summary} \n
        ################## 
        Above is a summary of a academic document to understand the what the academic document is about. \n
        The user is looking for specific information in the document. below is their search criteria containing everything the user is looking for from the document section. \n
        Context: Is the information the user is looking for in the document, if so return the information found in the document. \n
        Keywords: Are the exact keywords that the user is looking for in the document. \n
        Similar Keywords: are synonyms or related concepts to the keywords that are in the document based on the context.\n \n
        I will share with you a sections from the document, your job is to look for anything in that section that the user may find useful  using the information in the "search criteria" extract as much information as possible.  Then return as many  extracted information from that section as possible in a json format. \n
        Below is the section of Content from the academic research paper document, please read it carefully \n 
       
        \n \n
        # DOCUMENT SECTION \n
        # Current Document Section Content Below: \n
        {text} \n\n 
         ###################### \n

        Note: The Document Section Content Above is one part of the Academic Document, Focus your analysis only on the "Current Document Section" above, and extract as much information as possible from the documentation the user will find imporant.
        
        ## Your goal is to use the Search Criterias below provided by the user to search the Document Current Section and determine if it is anything relevant to the user Search Criterias. \n

        Task: Analyze the current section document against the search criteria extract as many json formated responses as possible:
        1. Context Match: Ask yourself Does the document section have any relation to the context asked by the user? If yes, extract the exact matching text and the whole sentance for context from the section in full, with citations (e.g [44]/ (John, 2018)) or sources. \n
        2. Keyword Match: Ask yourself Does the section contain any exact keywords? If yes, extract the sentence containing the keyword from the section. \n
        3. similar Concepts: Does the section contain related concepts? If yes, extract the relevant text. \n

        Below is the User Search Query, the context is what the user is looking for from the section of the academic paper above.


        --------------------------- \n
        # USER SEARCH CRITERIA: \n
        **Context:** \n
        {context} \n\n
        **Keywords:** \n
        {keywords_str} \n\n 
        
         ---------------------------

        - Your goal is to use the Search Criterias above given by the user to analyse the Document Section Content and determine if any of it is relevant to the user based on the search criteria. \n
        - The "context" can contain questions from the user, or information the user is looking for. If the context is a question check the Current Document Section Content to see if it answers any of the questions. If yes, extract any many matching text and the whole sentance from the section document in full with its citations or sources. \n
        - The "context" can also be information or a statment made by the user, If the context is a information or a statment made by the user check the Current Document Section Content that any part of the user context(search criteria) is relevant this could be a supporting statement or a opposing statement both is considered relevant match, return as many as possible if found. \n
        - For "Keywords" Ask yourself Does the section contain any exact keywords? If yes, extract the sentence containing the keyword from the section.\n
        - For "Similar Keyword" Ask yourself Does the section contain any phrase and words with similar meaning to th keywords the user searching for? If yes, extract the sentence containing the simluar keyword from the section \n \n
        --------------------------- \n

        # RESPONSE
        Must always Return JSON response format as many matches as possible from the section document  :\n 
        has_context: bool, 
        context: str ,
        has_keyword: bool, 
        has_similar_keyword: bool, 
        keyword: str ,
        similar_keyword: str ,
        keyword_context: str, \n 

        IMPORTANT: Return ALL matches found in the section. Each match should be a separate object in the responses array.
        For each relevant piece of text found:
        - If it matches the context, return the full sentance for full context
        - If it contains keywords, include it as a separate match, include the keyword found and in the keyword_context include the sentance the keyword was found
        - If it contains similar concepts to the keyword, include it as a separate match,  include the found concept and in the keyword_context include the sentance the simliar concept was found
        
        
        ---------------------------
        **JSON Response Format:**  
        Each relevant match should be returned as a **separate object** in the `responses` array.  
        If a section document contains multiple matches or relevant information, return **each match as a distinct object**. \n
        
         # EXAMPLE 1:\n
        ```json
        {"""
            "responses": [
                {{
                    "has_context": true, 
                    "context": "Extracted relevant sentence with citation [12].",  
                    "has_keyword": true, 
                    "has_similar_keyword": false, 
                    "keyword": "example_keyword",  
                    "similar_keyword": "",  
                    "keyword_context": "Full sentence containing example_keyword."
                }},
                {{
                    "has_context": false,  
                    "context": "",  
                    "has_keyword": true,  
                    "has_similar_keyword": false,  
                    "keyword": "another_keyword",  
                    "similar_keyword": "",  
                    "keyword_context": "Sentence containing another_keyword."
                }},
                {{
                    "has_context": true,  
                    "context": "A sentence that is relevant to the user’s search context, with citation [5].",  
                    "has_keyword": false,  
                    "has_similar_keyword": false,  
                    "keyword": "",  
                    "similar_keyword": "",  
                    "keyword_context": ""
                }},
                {{
                    "has_context": true,  
                    "context": "A statement discussing a related topic relevant to the user's search query.",  
                    "has_keyword": true,  
                    "has_similar_keyword": true,  
                    "keyword": "original_keyword",  
                    "similar_keyword": "related_concept",  
                    "keyword_context": "Sentence containing both original_keyword and related_concept."
                }}
            ]
        """}
        ```

        # EXAMPLE 2:\n
                {"""
                    {
                        "responses": [
                            {
                                "has_context": true,
                                "context": "A legume that\\'s high in protein and fiber, and also contains B vitamins, iron, and potassium [8].",
                                "has_keyword": true,
                                "has_similar_keyword": false,
                                "keyword": "fiber",
                                "similar_keyword": "",
                                "keyword_context":" A legume that\\'s high in protein and fiber"
                            },
                            {
                                "has_context": false,
                                "context": "",
                                "has_keyword": true,
                                "has_similar_keyword": false,
                                "keyword": "zinc.",
                                "similar_keyword": ""
                                 "keyword_context": "Plant-based proteins that also contain iron and zinc.",
                            },
                            {
                                "has_context": true,
                                "context": "With the addition of protein an essential nutrient that helps build and repair body tissue [34, 50], maintain muscle strength, and heal wounds.",
                                "has_keyword": false,
                                "has_similar_keyword": false,
                                "keyword": "",
                                "similar_keyword": "",
                                "keyword_context": ""
                            },
                            {
                                "has_context": true,
                                "context": "A quick snack that contains protein, fiber, magnesium, zinc, and polyunsaturated fatty acids [12]. A complete protein that contains all the essential amino acids, as well as omega-3 fatty acids, iron, and fiber.  [10, 15, 52]. ",
                                "has_keyword": true,
                                "has_similar_keyword": false,
                                "keyword": "fiber, zinc",
                                "similar_keyword": "",
                                "keyword_context": "A quick snack that contains protein, fiber, magnesium, zinc, and polyunsaturated fatty acids [12]."
                            }
                        ]
                    }
                    """}

         ###################
        """
        
        print(f"[DocumentSearcher] Prompt constructed, length: {len(prompt)}")
        return prompt


    # def analyze_section(
    #     self,
    #     section: Dict,
    #     context: str,
    #     keywords: List[str],
    #     summary: str,
    #     ) -> Dict:
    #         """Analyze section with context awareness
            
    #         Input:
    #             section: {
    #                 'content': {
    #                     'text': str,
    #                     'type': str,
    #                     'has_citations': bool
    #                 },
    #                 'prev_page_text': Optional[str],
    #                 'next_page_text': Optional[str]
    #             }
    #         """
    #         print("\n[DocumentSearcher] Starting section analysis: \n", section )

    #         # Get main text with context
    #         analysis_text = []
                
    #         analysis_text.append(section['text'])
            
    #         full_text = "\n".join(analysis_text)
            
    #         prompt = self._construct_search_prompt(
    #             full_text, context, keywords, summary
    #         )
    #         print(f"[DocumentSearcher] Search prompt: \n {prompt}")

                
    #         function_schema = {
    #             "name": "analyse_section_content",
    #             "parameters": SearchResults.schema()
    #         }

    #         print("[DocumentSearcher] Calling OpenAI API")
    #         response = self.llm.chat.completions.create(
    #             model="gpt-4o-mini",
    #             messages=[{
    #                 "role": "system",
    #                 "content": prompt
    #             }],
    #             temperature=0.3,
    #             functions=[function_schema],
    #             function_call={"name": "analyse_section_content"}
    #         )
                
            
    #         prompt_tokens = response.usage.prompt_tokens
    #         completion_tokens = response.usage.completion_tokens
    #         total_tokens = response.usage.total_tokens
    #         # Track API usage
    #         self.total_tokens_used += total_tokens
    #         self.total_api_calls += 1

    #         print(f"[DocumentSearcher] API call completed, tokens used: {response.usage.total_tokens}")
    #         print(f"[DocumentSearcher] prompt_tokens", prompt_tokens)
    #         print(f"[DocumentSearcher] completion_tokens", completion_tokens)
    #         print(f"[DocumentSearcher] total_tokens", self.total_tokens_used)
    #         # print(f"[DocumentSearcher] estimated_cost", AIModelCosts.calculate_cost(
    #         #     total_tokens, 
    #         #     "gpt4-mini",
    #         #     is_cached=False,
    #         #     is_batch=False
    #         # ))
        
    #         # print("full Response: ", response)
    #         results = json.loads(response.choices[0].message.function_call.arguments)
    #         print(f"[DocumentSearcher] API response received:", results)
    #         validated_results = SearchResults(**results)

    #         for idx, match in enumerate(validated_results.responses):
    #             print(f"Match {idx + 1}:")
    #             if match.has_context:
    #                 print(f"  Context: {match.context}")
    #             if match.has_keyword:
    #                 print(f"  Keyword: {match.keyword}")
    #                 print(f"  Keyword Context: {match.keyword_context}")
    #             if match.has_similar_keyword:
    #                 print(f"  Similar Keyword: {match.similar_keyword}")
                
                
    #         return validated_results.model_dump()

    def analyze_section(
        self,
        section: Dict,
        context: str,
        keywords: List[str],
        summary: str,
        document_id: str = None  # Add document_id parameter
        ) -> Dict:
            """Analyze section with context awareness"""
            print("\n[DocumentSearcher] Starting section analysis")
            
            # Start timing
            start_time = timezone.now()
            
            # Get main text with context
            analysis_text = []
            analysis_text.append(section['text'])
            full_text = "\n".join(analysis_text)
            
            prompt = self._construct_search_prompt(
                full_text, context, keywords, summary
            )
            print(f"[DocumentSearcher] Search prompt length: {len(prompt)}")
                
            function_schema = {
                "name": "analyse_section_content",
                "parameters": SearchResults.schema()
            }

            print("[DocumentSearcher] Calling OpenAI API")
            model_name = "gpt-4o-mini"  # Set the model name here - could be configurable
            
            try:
                response = self.llm.chat.completions.create(
                    model=model_name,
                    messages=[{
                        "role": "system",
                        "content": prompt
                    }],
                    temperature=0.3,
                    functions=[function_schema],
                    function_call={"name": "analyse_section_content"}
                )
                
                # End timing
                end_time = timezone.now()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # Calculate costs
                from .ai_tracking.model_costs import AIModelCosts
                
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
                
                # Track API usage
                cost_info = AIModelCosts.calculate_cost(
                    prompt_tokens, 
                    completion_tokens, 
                    model_name
                )
                
                # Create usage record
                usage_record = {
                    'model_name': model_name,
                    'prompt': prompt,
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens,
                    'cost_per_1k_prompt_tokens': cost_info['cost_per_1k_prompt'],
                    'cost_per_1k_completion_tokens': cost_info['cost_per_1k_completion'],
                    'total_cost': cost_info['total_cost'],
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_ms': duration_ms,
                    'document_id': document_id
                }
                
                self.api_usage_records.append(usage_record)
                
                # Track total usage
                self.total_tokens_used += total_tokens
                self.total_api_calls += 1

                print(f"[DocumentSearcher] API call completed, tokens used: {total_tokens}")
                print(f"[DocumentSearcher] prompt_tokens: {prompt_tokens}")
                print(f"[DocumentSearcher] completion_tokens: {completion_tokens}")
                print(f"[DocumentSearcher] total_tokens: {self.total_tokens_used}")
                print(f"[DocumentSearcher] duration_ms: {duration_ms}")
                print(f"[DocumentSearcher] total_cost: ${cost_info['total_cost']:.6f}")
            
                content = response.choices[0].message.function_call.arguments
                results = json.loads(content)
                print(f"[DocumentSearcher] API response received")
                validated_results = SearchResults(**results)

                for idx, match in enumerate(validated_results.responses):
                    print(f"Match {idx + 1}:")
                    if match.has_context:
                        print(f"  Context: {match.context}")
                    if match.has_keyword:
                        print(f"  Keyword: {match.keyword}")
                        print(f"  Keyword Context: {match.keyword_context}")
                    if match.has_similar_keyword:
                        print(f"  Similar Keyword: {match.similar_keyword}")
                    
                return validated_results.model_dump()
            
            except Exception as e:
                # End timing for error case
                end_time = timezone.now()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                print(f"[DocumentSearcher] API call failed: {str(e)}")
                
                # Record error
                self.api_usage_records.append({
                    'model_name': model_name,
                    'prompt': prompt,
                    'prompt_tokens': 0,  # Can't know token count on error
                    'completion_tokens': 0,
                    'total_tokens': 0,
                    'cost_per_1k_prompt_tokens': 0,
                    'cost_per_1k_completion_tokens': 0,
                    'total_cost': 0,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_ms': duration_ms,
                    'document_id': document_id,
                    'error': str(e)
                })
                
                # Re-raise for proper error handling
                raise

    def calculate_relevance_score(
    self,
    total_sections: int,
    context_matches: int,
    keyword_matches: int,
    similar_matches: int,
    document_relevance: bool
) -> float:
        """Calculate relevance score with detailed monitoring"""
        print("\n[DocumentSearcher] Calculating relevance score")

        print(f"[DocumentSearcher] Total sections: {total_sections}")
        print(f"[DocumentSearcher] Context matches: {context_matches}")
        print(f"[DocumentSearcher] Keyword matches: {keyword_matches}")
        print(f"[DocumentSearcher] similar keyword matches: {similar_matches}")
        
        # Calculate components with adjusted weights
        context_score = (context_matches) * 15  # Increased weight for context
        keyword_score = (keyword_matches) * 5   # Adjusted weight for keywords
        similar_score = (similar_matches) * 2    # Adjusted weight for similar matches
        summary_bonus = 5 if document_relevance else 0  # Adjusted summary bonus
        
        # Calculate total
        total_score = context_score + keyword_score + similar_score + summary_bonus
        final_score = min(total_score, 100.0)
        
        print("[DocumentSearcher] Score components:")
        print(f"  Context score: {context_score:.2f}")
        print(f"  Keyword score: {keyword_score:.2f}")
        print(f"  similar concepts score: {similar_score:.2f}")
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

        if self.llm is None:
            print(f"[DocumentSearcher] Cannot check summary relevance: OpenAI client initialization failed: {getattr(self, '_init_error', 'Unknown error')}")
            return False
        
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
        # print(f"[DocumentSearcher] estimated_cost", AIModelCosts.calculate_cost(
        #     total_tokens, 
        #     "gpt4-mini",
        #     is_cached=False,
        #     is_batch=False
        # ))

        
        is_relevant = response.choices[0].message.content.strip().lower() == "true"
        print(f"[DocumentSearcher] Summary relevance result: {is_relevant}")
        
        return is_relevant


    def search_document(
    self,
    sections: List[Dict],
    context: str,
    keywords: List[str],
    summary: str,  
    reference_data: Dict,
    document_id: str = None  # Add document_id parameter
    ) -> Dict:
        """Search document with page-based sections"""
        print("\n[DocumentSearcher] Starting document search")
        print(f"[DocumentSearcher] Processing {len(sections)} pages")
        
        # Reset usage records for this document
        self.api_usage_records = []

        matches = {
            "context": 0,
            "keyword": 0,
            "similar": 0,
            "relevant_sections": [],
            "relevance_score": 0,
            "total_matches": 0
        }

        # Process each section
        for section in sections:
            results = self.analyze_section(
                section=section,
                context=context,
                keywords=keywords,
                summary=summary,
                document_id=document_id  # Pass the document_id
            )
            print("[DocumentSearcher] Search Results: ", results)

            # Initialize section data
            section_matches = {

                'page_number': section['page_number'],
                'section_id': section['section_id'],
                'start_text': section['start_text'],
                'context_matches': [],    # Separate array for context matches
                'keyword_matches': [],    # Separate array for keyword matches
                'similar_matches': []     # Separate array for similar matches
            }

            # Process each match type separately
            for match in results.get('responses', []):
                # Context matches
                if match['has_context']:
                    print("Has Matching Context ")
                    matches["context"] += 1
                    print("Has Matching Context Text: \n", match["context"])
                    section_matches['context_matches'].append({
                        'text': match["context"],
                        'citations': self._extract_citations(match['context'], reference_data)
                    })

                # Keyword matches
                if match['has_keyword']:
                    matches["keyword"] += 1
                    print("Has Matching Keywords ")
                    print("Has Matching Keywords Text:  ", match['keyword'] )
                    section_matches['keyword_matches'].append({
                        'keyword': match['keyword'],
                        'text': match['keyword_context']
                    })


                # Similar keyword matches
                if match['has_similar_keyword']:
                    matches["similar"] += 1
                    section_matches['similar_matches'].append({
                        'similar_keyword': match['similar_keyword'],
                        'text': match['keyword_context']
                    })

            # Only add sections with matches
            if (section_matches['context_matches'] or 
                section_matches['keyword_matches'] or 
                section_matches['similar_matches']):
                matches["relevant_sections"].append(section_matches)

        # Calculate relevance
        
        is_relevant = self.check_summary_relevance(summary, context)
        relevance_score = self.calculate_relevance_score(
            total_sections=len(sections),
            context_matches=matches["context"],
            keyword_matches=matches["keyword"],
            similar_matches=matches["similar"],
            document_relevance=is_relevant
        )

        matches["relevance_score"] = relevance_score
        matches["total_matches"] = sum([
            len(section['context_matches']) +
            len(section['keyword_matches']) +
            len(section['similar_matches'])
            for section in matches["relevant_sections"]
        ])

        return {
            'context_matches': matches["context"],
            'keyword_matches': matches["keyword"],
            'similar_matches': matches["similar"],
            'relevant_sections': matches["relevant_sections"],
            'relevance_score': matches["relevance_score"],
            'total_matches': matches["total_matches"],
            'api_usage': self.api_usage_records  # Add this to return API usage
        }
    

    def _extract_citations(self, text: str, reference_data: Dict) -> List[Dict]:
        """Extract citations from text and link to references
        
        Input:
            text: str - Text containing citations
            reference_data: Dict - Reference data dictionary
            
        Output:
            List[Dict] - List of found citations with references in same format as document processor
        """
        try:
            # Use the cleaned text approach
            cleaned_text = re.sub(r'\s+', ' ', text).strip()
            citations = []
            
            # Extract numbered citations with comma separation - matching document processor format
            for match in re.finditer(r'\[(\d+(?:,\s*\d+)*)\]', cleaned_text):
                citation_text = match.group(0)
                ref_numbers = [num.strip() for num in match.group(1).split(',')]
                
                citation_data = {
                    'text': citation_text,
                    'type': 'numbered',
                    'position': match.span(),
                    'ref_numbers': ref_numbers,
                    'references': []
                }
                
                # Match references just like document processor
                if reference_data and 'entries' in reference_data:
                    for ref_num in ref_numbers:
                        if ref_num in reference_data['entries']:
                            citation_data['references'].append(
                                reference_data['entries'][ref_num]
                            )
                
                citations.append(citation_data)
            print("search citations: \n", citations)
            return citations
            
        except Exception as e:
            print(f"[DocumentSearcher] Citation extraction error: {str(e)}")
            return []

         


        