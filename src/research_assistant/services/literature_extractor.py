# # src/research_assistant/services/literature_extractor.py

# from typing import Dict, List, Any, Optional
# import json
# from openai import OpenAI
# from django.conf import settings
# from pydantic import BaseModel, Field
# import re
# import time
# import logging
# from .document_processor import DocumentProcessor

# # Define Pydantic model for structured data extraction
# class KeyQuote(BaseModel):
#     text: str
#     citation_data: Dict = None
#     page: int

# class researchApproach(BaseModel):
#     description: str
#     page: int

# class MethodApproach(BaseModel):
#     study_design: str = Field(..., description="minimum of 200 words, In as much detail as possible explaining the design of the study, You must walk the user through the design of the study in a way that they can implement it or easy to understand it.  minimum of 200 words")
#     participants: str  = Field(..., description="Details about the participants, how they were selected, the number, and any other relevant information")
#     data_collection: str = Field(..., description="Methods used to collect data, tools, and techniques  AND any other relevant information")
#     data_analysis: str = Field(..., description="Approaches used to analyze data, transformation, statistical methods, and any other relevant information")
#     key_quotes: List[KeyQuote] = Field([], description="Exact as many quotes from the document that are important for this Method section(word for word quotes)")

# class Finding(BaseModel):
#     description: str = Field(..., description=" List all the results, Extract all the Results and the key findings from the document, It is important to explain the meaning of the findings and results and how it came to be from the method. All ket results must be explained in detail. List all the results, minimum of 300 words")
#     significance: str = Field(..., description="Why it matters")
#     key_quotes: List[KeyQuote] = Field([], description="Exact as many quotes from the document that are important for this Findings section(word for word quotes)")
#     page: int = Field(..., description="Page number where the quote was found")

# class StrengthLimitation(BaseModel):
#     description: str  = Field(..., description="Strength or limitation description")
#     key_quotes: List[KeyQuote] = Field([], description="Exact the quote that backs up the description (word for word quotes)")
#     page: int = Field(..., description="Page number where the quote was found")

# class LiteratureReviewData(BaseModel):
#     research_area: str = Field(..., description=" minimum of 100 words, Identify the specific field or subfield (which area is this reseach taking place in? (Including a difinition of the research area). minimum of 200 words")
#     themes: List[str] = Field(..., description=" Exact a list of Themes or subtopics found in the document these themes should be based on the different subject and content and topics the document covers")
#     chronological_development: Optional[researchApproach] = Field(None, description="Chronological Development (how the research has builds on previous work)")
#     theoretical_frameworks: Optional[researchApproach] = Field(None, description="Theoretical Frameworks (the theories underpinning this research)")
#     methodological_approaches: MethodApproach  = Field(..., description="Detailed breakdown of methods explain in as much detail as possible. Include Study Design, Participants, Data Collection, and Data Analysis. You must walk the user through the design of the study in a way that they can implement it or easy to understand it. minimum of 100 words ")
#     key_findings: List[Finding] = Field(..., description="Should list all the findings, results, Extract all the key findings from the document including the significance of each finding and any key quotes that support the findings. It is important to explain the meaning of the findings and how it came to be from the method.  minimum of 300 words")
#     method_strengths: List[StrengthLimitation] = Field(..., description="List as many methodological strengths (2-5)")
#     method_limitations: List[StrengthLimitation] = Field(..., description="List as many methodological limitations (2-5)")
#     result_strengths: List[StrengthLimitation] = Field(..., description="List as many strengths of findings (2-5)")
#     result_weaknesses: List[StrengthLimitation] = Field(..., description="List as many weaknesses of findings (2-5)")
#     potential_biases: List[StrengthLimitation] = Field(..., description="List as many potential biases or limitations")

# class LiteratureExtractor:
#     """Extract structured literature review data from research papers"""
    
#     def __init__(self):
#         print("[LiteratureExtractor] Initializing extractor")
#         try:
#             # Initialize OpenAI client following same pattern as document_searcher.py
#             import importlib.metadata
#             version = importlib.metadata.version("openai")
#             major_version = int(version.split('.')[0])
#             print(f"[LiteratureExtractor] Detected OpenAI version: {version}")
            
#             # Initialize with proxy handling for Railway
#             try:
#                 # Standard initialization that might fail with 'proxies' parameter in Railway
#                 self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
#                 print(f"[LiteratureExtractor] Using OpenAI API v{major_version}.x")
#             except TypeError as e:
#                 # Specifically handle the proxies error in Railway
#                 if 'proxies' in str(e):
#                     print("[LiteratureExtractor] Detected proxy configuration, using alternate initialization")
#                     import httpx
#                     # Create a custom HTTP client without proxies
#                     http_client = httpx.Client(timeout=300)  # Longer timeout for large documents
#                     self.llm = OpenAI(
#                         api_key=settings.OPENAI_API_KEY,
#                         http_client=http_client  # Use custom client without proxies
#                     )
#                 else:
#                     raise
                    
#             print("[LiteratureExtractor] OpenAI client initialized successfully")
#         except Exception as e:
#             print(f"[LiteratureExtractor] CRITICAL ERROR initializing OpenAI client: {str(e)}")
#             self.llm = None
#             self._init_error = str(e)
        
#         self.total_tokens_used = 0
#         self.total_api_calls = 0
#         print("[LiteratureExtractor] Initialization complete")

#     def _construct_extraction_prompt(self, document_text: str) -> str:
#         """Construct prompt for extracting literature review data"""
#         print(f"[LiteratureExtractor] Constructing extraction prompt for document of length {len(document_text)}")
        
#         prompt = f"""
#         # TASK: RESEARCH PAPER ANALYSIS
#         You are an expert academic researcher, specializing in extracting structured information from research papers. Your goal is to help extract as much information as possible from the research paper


#         \n\n
#         # RESEARCH PAGE/DOCUMENT TEXT (with page markers):
#         {document_text} \n\n
#         DOCUMENT TEXT ENDS HERE..\n\n
#         {'############################################## \n\n' * 4}
    
        
#         Analyze this academic paper and extract the following information in a STRUCTURED FORMAT:
        
#         1. Research Area: minimum of 100 words. Identify the specific field or subfield (which area is this reseach taking place in? Including a difinition of the research area. minimum of 100 words)
        
#         2. Themes & Subtopics: Extract a list of Themes or subtopics found in the document these themes should be based on the different subject and content and topics the document covers
        
#         3. Document Development: Extract ATLEAST ONE of the following (ALL If prominent):
#            - Chronological Development (how the research has builds on previous work)
#            - Theoretical Frameworks (the theories underpinning this research)
#            - Methodological Approaches (detailed breakdown of methods explain in as much detail as possible. minimum of 300 words, the whole process)
        
#         4. Methodological Information: (This is the most important part of the extraction, ensure to get as much detail as possible)
#            - Study Design: (In as much detail as possible explaining the design of the study, You must walk the user through the design of the study in a way that they can implement it or easy to understand it, minimum of 200 words).
#            - Participants: (Details about the participants, how they were selected, the number, and any other relevant information).
#            - Data Collection: (Methods used to collect data, tools, and techniques  AND any other relevant information).
#            - Data Analysis: (Approaches used to analyze data, transformation, statistical methods, and any other relevant information).
        
#         5. Key Findings: List all the results, metics and findings. In a minimum of 300 words, Extract ALL the results from the study and key findings including the significance of each finding and any key quotes that support the findings. It is important to explain the meaning of the findings and how it came to be from the method.  List all the results,  minimum of 300 words
        
#         6. Critical Analysis:
#            - Method Strengths: list as many methodological strengths (2-5)
#            - Method Limitations: list as many methodological limitations (2-5)
#            - Result Strengths: list as many strengths of findings (2-5)
#            - Result Weaknesses: list as many weaknesses of findings (2-5)
#            - Potential Biases:  list as many potential biases or limitations 
        
#         IMPORTANT INSTRUCTIONS:
#         - Ensure to provide detailed information for each section as much as possible, You MUST ADHERE TO THE WORD COUNT FOR THE SECTION. Explain clarely in as much detail for the user to understand the whole research.
#         - For each section, include PAGE NUMBER where the information was found
#         - For important statements, extract the EXACT TEXT and any CITATIONS in the text word for word
#         - Must provide as must detail so the user have a clear understannding of the whole research.
#         - Focus especially on detailed methodological information 
#         - Maintain logical flow from methods to results/findings
#         - Make complex methods, easy to understand walking though the steps for implementation
#         \n\n
        
#         # OUTPUT FORMAT: (For each section, provide as much detail as possible)
#         Return a structured JSON object following this schema (example values shown):
#         ```json
#          {"""
#                 {
#                 "research_area": {
#                     "description": "Identify the specific field or subfield of the research, including a definition of the research area. Explain in as much detail as possible.",
#                     "page": "Page number where this information is found."
#                 },
#                 "themes": [
#                     {
#                     "theme": "Exact a list of Themes or subtopics found in the document these themes should be based on the different subjects and topics the document covers",
#                     "page": "Page number where this theme appears."
#                     }
#                 ],
#                 "chronological_development": {
#                     "description": "Explanation of how the research builds on previous work, if present.",
#                     "page": "Page number where this is discussed."
#                 },
#                 "theoretical_frameworks": {
#                     "description": "Theoretical frameworks underpinning the research, if present.",
#                     "page": "Page number where this is discussed."
#                 },
#                 "methodological_approaches": {
#                     "study_design": {
#                     "description": "Detailed explanation of the study design.",
#                     "page": "Page number where this is discussed."
#                     },
#                     "participants": {
#                     "description": "Details about the participants, how they were selected, the number, and any other relevant information.",
#                     "page": "Page number where this is discussed."
#                     },
#                     "data_collection": {
#                     "description": "Methods used to collect data, including tools and techniques.",
#                     "page": "Page number where this is discussed."
#                     },
#                     "data_analysis": {
#                     "description": "Approaches used to analyze data, including statistical methods or transformations.",
#                     "page": "Page number where this is discussed."
#                     },
#                     "key_quotes": [
#                     {
#                         "text": "Exact quote from the document relevant to methodology.",
#                         "citation_data": "Citation information if available.",
#                         "page": "Page number where the quote appears."
#                     }
#                     ]
#                 },
#                 "key_findings": [
#                     {
#                     "description": "Detailed explanation of all the finding, metrics and results explain all the results and the key findings.",
#                     "significance": "Why this finding is important/ relation to the method.",
#                     "key_quotes": [
#                         {
#                         "text": "Exact quote supporting the finding.",
#                         "citation_data": "Citation information if available.",
#                         "page": "Page number where the quote appears."
#                         }
#                     ],
#                     "page": "Page number where this finding is discussed."
#                     },
#                     {
#                     "description": "Detailed explanation of all the finding, metrics and results  explain all the results and the key findings.",
#                     "significance": "Why this finding is important/ relation to the method.",
#                     "key_quotes": [
#                         {
#                         "text": "Exact quote supporting the finding.",
#                         "citation_data": "Citation information if available.",
#                         "page": "Page number where the quote appears."
#                         }
#                     ],
#                     "page": "Page number where this finding is discussed."
#                     }
#                 ],
#                 "method_strengths": [
#                     {
#                     "description": "Detailed explanation of a methodological strength.",
#                     "key_quotes": [
#                         {
#                         "text": "Exact quote supporting the strength.",
#                         "citation_data": "Citation information if available.",
#                         "page": "Page number where the quote appears."
#                         }
#                     ],
#                     "page": "Page number where this is discussed."
#                     }
#                 ],
#                 "method_limitations": [
#                     {
#                     "description": "Detailed explanation of a methodological limitation.",
#                     "key_quotes": [
#                         {
#                         "text": "Exact quote supporting the limitation.",
#                         "citation_data": "Citation information if available.",
#                         "page": "Page number where the quote appears."
#                         }
#                     ],
#                     "page": "Page number where this is discussed."
#                     }
#                 ],
#                 "result_strengths": [
#                     {
#                     "description": "Explanation of a strength in the research results.",
#                     "key_quotes": [
#                         {
#                         "text": "Exact quote supporting the result strength.",
#                         "citation_data": "Citation information if available.",
#                         "page": "Page number where the quote appears."
#                         }
#                     ],
#                     "page": "Page number where this is discussed."
#                     }
#                 ],
#                 "result_weaknesses": [
#                     {
#                     "description": "Explanation of a weakness in the research results.",
#                     "key_quotes": [
#                         {
#                         "text": "Exact quote supporting the result weakness.",
#                         "citation_data": "Citation information if available.",
#                         "page": "Page number where the quote appears."
#                         }
#                     ],
#                     "page": "Page number where this is discussed."
#                     }
#                 ],
#                 "potential_biases": [
#                     {
#                     "description": "Explanation of potential biases or limitations in the study.",
#                     "key_quotes": [
#                         {
#                         "text": "Exact quote supporting the bias/limitation.",
#                         "citation_data": "Citation information if available.",
#                         "page": "Page number where the quote appears."
#                         }
#                     ],
#                     "page": "Page number where this is discussed."
#                     }
#                 ]
#                 } \n\n
          
#        1. Research Area: minimum of 100 words. Identify the specific field or subfield (which area is this reseach taking place in? Including a difinition of the research area. minimum of 100 words)
        
#         2. Themes & Subtopics: Extract a list of Themes or subtopics found in the document these themes should be based on the different subject and content the document covers
        
#         3. Document Development: Extract ATLEAST ONE of the following (ALL If prominent):
#            - Chronological Development (how the research has builds on previous work)
#            - Theoretical Frameworks (the theories underpinning this research)
#            - Methodological Approaches (detailed breakdown of methods explain in as much detail as possible. minimum of 300 words, the whole process)
        
#         4. Methodological Information: (This is the most important part of the extraction, ensure to get as much detail as possible)
#            - Study Design: (In as much detail as possible explaining the design of the study, You must walk the user through the design of the study in a way that they can implement it or easy to understand it, minimum of 200 words).
#            - Participants: (Details about the participants, how they were selected, the number, and any other relevant information).
#            - Data Collection: (Methods used to collect data, tools, and techniques  AND any other relevant information).
#            - Data Analysis: (Approaches used to analyze data, transformation, statistical methods, and any other relevant information).
        
#         5. Key Findings: List all the results, metics and findings. In a minimum of 300 words, Extract ALL the results from the study and key findings including the significance of each finding and any key quotes that support the findings. It is important to explain the meaning of the findings and how it came to be from the method.  List all the results,  minimum of 300 words
        
#         6. Critical Analysis:
#            - Method Strengths: list as many methodological strengths (2-5)
#            - Method Limitations: list as many methodological limitations (2-5)
#            - Result Strengths: list as many strengths of findings (2-5)
#            - Result Weaknesses: list as many weaknesses of findings (2-5)
#            - Potential Biases:  list as many potential biases or limitations \n
        
          
          
#         IMPORTANT: You MUST ADHERE TO THE WORD COUNT FOR THE SECTION. Ensure to provide detailed information for each section as much  as possible, explain clarely in as much detail for the user to understand the whole research.

#         """}
#         ```
#         """
        
#         print(f"[LiteratureExtractor] Prompt constructed with length: {len(prompt)}")
#         return prompt

#     def _append_sections_with_page_markers(self, sections: List) -> str:
#         """Combine document sections with clear page markers"""
#         combined_text = ""
        
#         for section in sections:
#             # Access attributes directly on the model instance
#             page_num = section.section_start_page_number
#             content = section.content
            
#             if content:
#                 combined_text += f"\n\n--- START PAGE {page_num} ---\n\n{content} \n\n--- END PAGE {page_num} ---\n\n"
        
#         return combined_text

#     def _extract_citations(self, text: str, reference_data: Dict[str, Any]) -> Dict:
#         """Extract citations from text using the same approach as document_searcher"""
#         try:
#             # Use the existing citation extraction pattern
#             cleaned_text = re.sub(r'\s+', ' ', text).strip()
            
#             # First handle numbered citations
#             citation_data = None
#             for match in re.finditer(r'\[(\d+(?:,\s*\d+)*)\]', cleaned_text):
#                 citation_text = match.group(0)
#                 ref_numbers = [num.strip() for num in match.group(1).split(',')]
                
#                 citation_data = {
#                     'text': citation_text,
#                     'type': 'numbered',
#                     'position': match.span(),
#                     'ref_numbers': ref_numbers,
#                     'references': []
#                 }
                
#                 # Match references
#                 if reference_data and 'entries' in reference_data:
#                     for ref_num in ref_numbers:
#                         if ref_num in reference_data['entries']:
#                             citation_data['references'].append(
#                                 reference_data['entries'][ref_num]
#                             )
#                 break  # Just get the first citation for now
                
#             return citation_data
#         except Exception as e:
#             print(f"[LiteratureExtractor] Citation extraction error: {str(e)}")
#             return None

#     def extract_literature_review(self, document_id: str, sections: List, reference_data: Dict) -> Dict:
#         """Extract structured literature review data from document sections"""
#         print(f"[LiteratureExtractor] Starting extraction for document: {document_id}")
        
#         try:
#             # Combine all sections with page markers
#             combined_text = self._append_sections_with_page_markers(sections)
#             print(f"[LiteratureExtractor] Combined text length: {len(combined_text)}")
            
#             # Prepare extraction prompt
#             prompt = self._construct_extraction_prompt(combined_text)
            
#             # Call OpenAI API
#             print("[LiteratureExtractor] Calling OpenAI API")
#             start_time = time.time()
            
#             response = self.llm.chat.completions.create(
#                 model="gpt-4-1106-preview",  # or another suitable model with high context window
#                 messages=[{
#                     "role": "system",
#                     "content": prompt
#                 }],
#                 temperature=0.3,
#                 max_tokens=4000
#             )
            
#             print("[LiteratureExtractor] API call completed")
            
#             # Update token usage tracking
#             prompt_tokens = response.usage.prompt_tokens
#             completion_tokens = response.usage.completion_tokens
#             total_tokens = response.usage.total_tokens
#             self.total_tokens_used += total_tokens
#             self.total_api_calls += 1
            
#             print(f"[LiteratureExtractor] Tokens used: {total_tokens}")
#             print(f"[LiteratureExtractor] API calls: {self.total_api_calls}")
            
#             # Parse response
#             content = response.choices[0].message.content
            
#             # Extract JSON from content (in case there's additional text)
#             try:
#                 json_content = content
#                 if "```json" in content:
#                     json_content = content.split("```json")[1].split("```")[0].strip()
#                 elif "```" in content:
#                     json_content = content.split("```")[1].split("```")[0].strip()
                
#                 extracted_data = json.loads(json_content)
#                 print("[LiteratureExtractor] Successfully parsed JSON response")
                
#                 # Post-process to add citation data
#                 if 'methodological_approaches' in extracted_data and 'key_quotes' in extracted_data['methodological_approaches']:
#                     for quote in extracted_data['methodological_approaches']['key_quotes']:
#                         if 'text' in quote and not quote.get('citation_data'):
#                             quote['citation_data'] = self._extract_citations(quote['text'], reference_data)
                
#                 if 'key_findings' in extracted_data:
#                     for finding in extracted_data['key_findings']:
#                         if 'key_quotes' in finding:
#                             for quote in finding['key_quotes']:
#                                 if 'text' in quote and not quote.get('citation_data'):
#                                     quote['citation_data'] = self._extract_citations(quote['text'], reference_data)
                
#                 # Process other sections with key_quotes similarly
                
#                 duration = time.time() - start_time
#                 print(f"[LiteratureExtractor] Extraction completed in {duration:.2f}s")
                
#                 return {
#                     'document_id': document_id,
#                     'extraction_data': extracted_data,
#                     'processing_time': duration,
#                     'status': 'success'
#                 }
                
#             except json.JSONDecodeError as e:
#                 print(f"[LiteratureExtractor] JSON parsing error: {str(e)}")
#                 print(f"[LiteratureExtractor] Raw content: {content[:500]}...")
#                 return {
#                     'document_id': document_id,
#                     'status': 'error',
#                     'error_message': 'Failed to parse literature review data'
#                 }
                
#         except Exception as e:
#             print(f"[LiteratureExtractor] Extraction error: {str(e)}")
#             return {
#                 'document_id': document_id,
#                 'status': 'error',
#                 'error_message': str(e)
#             }





# src/research_assistant/services/literature_extractor.py

from typing import Dict, List, Any, Optional
import json
from openai import OpenAI
from django.conf import settings
from pydantic import BaseModel, Field
import re
import time
import logging
from .document_processor import DocumentProcessor

# Define Pydantic model for structured data extraction
class KeyQuote(BaseModel):
    text: str
    citation_data: Dict = None
    page: int = Field(..., description="Page number where the quote was found, INT type(just the number)")

class researchApproach(BaseModel):
    description: str
    page: int = Field(..., description="Page number where the quote was found, INT type(just the number)")

class MethodApproach(BaseModel):
    study_design: str = Field(..., description="minimum of 200 words, In as much detail as possible explaining the design of the study, You must walk the user through the design of the study in a way that they can implement it or easy to understand it.  minimum of 200 words")
    participants: str  = Field(..., description="Details about the participants, how they were selected, the number, and any other relevant information")
    data_collection: str = Field(..., description="Methods used to collect data, tools, and techniques  AND any other relevant information")
    data_analysis: str = Field(..., description="Approaches used to analyze data, transformation, statistical methods, and any other relevant information")
    key_quotes: List[KeyQuote] = Field([], description="Exact as many quotes from the document that are important for this Method section(word for word quotes)")

class Finding(BaseModel):
    description: str = Field(..., description=" List all the results, Extract all the Results and the key findings from the document, It is important to explain the meaning of the findings and results and how it came to be from the method. All ket results must be explained in detail. List all the results, minimum of 300 words")
    significance: str = Field(..., description="Why it matters")
    key_quotes: List[KeyQuote] = Field([], description="Exact as many quotes from the document that are important for this Findings section(word for word quotes)")
    page: int = Field(..., description="Page number where the quote was found, INT type(just the number)")

class StrengthLimitation(BaseModel):
    description: str  = Field(..., description="Strength or limitation description")
    key_quotes: List[KeyQuote] = Field([], description="Exact the quote that backs up the description (word for word quotes)")
    page: int = Field(..., description="Page number where the quote was found INT type(just the number)")

class LiteratureReviewData(BaseModel):
    research_area: str = Field(..., description=" minimum of 100 words, Identify the specific field or subfield (which area is this reseach taking place in? (Including a difinition of the research area). minimum of 200 words")
    themes: List[str] = Field(..., description=" Extract a list of Themes or subtopics found in the document these themes should be based on the different subject and content and topics the document covers str type(just the number) listing all the pages that topic shows up (e.g 1, 4, 16)")
    chronological_development: Optional[researchApproach] = Field(None, description="Chronological Development (how the research has builds on previous work)")
    theoretical_frameworks: Optional[researchApproach] = Field(None, description="Theoretical Frameworks (the theories underpinning this research)")
    methodological_approaches: MethodApproach  = Field(..., description="Detailed breakdown of methods explain in as much detail as possible. Include Study Design, Participants, Data Collection, and Data Analysis. You must walk the user through the design of the study in a way that they can implement it or easy to understand it. minimum of 100 words ")
    key_findings: List[Finding] = Field(..., description="Should list all the findings, results, Extract all the key findings from the document including the significance of each finding and any key quotes that support the findings. It is important to explain the meaning of the findings and how it came to be from the method.  minimum of 300 words")
    method_strengths: List[StrengthLimitation] = Field(..., description="List as many methodological strengths (2-5)")
    method_limitations: List[StrengthLimitation] = Field(..., description="List as many methodological limitations (2-5)")
    result_strengths: List[StrengthLimitation] = Field(..., description="List as many strengths of findings (2-5)")
    result_weaknesses: List[StrengthLimitation] = Field(..., description="List as many weaknesses of findings (2-5)")
    potential_biases: List[StrengthLimitation] = Field(..., description="List as many potential biases or limitations")



class LiteratureExtractor:
    """Extract structured literature review data from research papers"""
    
    # Define model configurations
    PRIMARY_MODEL = "gpt-4-turbo"
    FALLBACK_MODELS = [
        "gpt-4o-mini"  # Higher TPM limit (90,000 vs 10,000)
    ]
    
    def __init__(self):
        print("[LiteratureExtractor] Initializing extractor")
        try:
            # Initialize OpenAI client following same pattern as document_searcher.py
            import importlib.metadata
            version = importlib.metadata.version("openai")
            major_version = int(version.split('.')[0])
            print(f"[LiteratureExtractor] Detected OpenAI version: {version}")
            
            # Initialize with proxy handling for Railway
            try:
                # Standard initialization that might fail with 'proxies' parameter in Railway
                self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
                print(f"[LiteratureExtractor] Using OpenAI API v{major_version}.x")
            except TypeError as e:
                # Specifically handle the proxies error in Railway
                if 'proxies' in str(e):
                    print("[LiteratureExtractor] Detected proxy configuration, using alternate initialization")
                    import httpx
                    # Create a custom HTTP client without proxies
                    http_client = httpx.Client(timeout=300)  # Longer timeout for large documents
                    self.llm = OpenAI(
                        api_key=settings.OPENAI_API_KEY,
                        http_client=http_client  # Use custom client without proxies
                    )
                else:
                    raise
                    
            print("[LiteratureExtractor] OpenAI client initialized successfully")
        except Exception as e:
            print(f"[LiteratureExtractor] CRITICAL ERROR initializing OpenAI client: {str(e)}")
            self.llm = None
            self._init_error = str(e)
        
        self.total_tokens_used = 0
        self.total_api_calls = 0
        print("[LiteratureExtractor] Initialization complete")

    def estimate_token_count(self, text_length):
        """Estimate the number of tokens based on text length"""
        # Rough estimate: 1 token ≈ 4 characters in English
        return text_length // 4

    def select_appropriate_model(self, document_length):
        """Select the appropriate model based on document size"""
        estimated_tokens = self.estimate_token_count(document_length)
        
        # Check if primary model can handle it (allowing some buffer for prompt overhead)
        if estimated_tokens < 28000:  # 30k limit - buffer
            return self.PRIMARY_MODEL
        
        # Try fallback model if estimated tokens are within their limit
        if estimated_tokens < 85000:  # 90k limit - buffer
            return self.FALLBACK_MODELS[0]
            
        # Document too large for any model
        return None

    def _construct_extraction_prompt(self, document_text: str) -> str:
        """Construct prompt for extracting literature review data"""
        print(f"[LiteratureExtractor] Constructing extraction prompt for document of length {len(document_text)}")
        
        prompt = f"""
        # TASK: RESEARCH PAPER ANALYSIS
        You are an expert academic researcher, specializing in extracting structured information from research papers. Your goal is to help extract as much information as possible from the research paper


        \n\n
        # RESEARCH PAGE/DOCUMENT TEXT (with page markers):
        {document_text} \n\n
        DOCUMENT TEXT ENDS HERE..\n\n
        {'############################################## \n\n' * 4}
    
        
        Analyze this academic paper and extract the following information in a STRUCTURED FORMAT:
        
        1. Research Area: minimum of 100 words. Identify the specific field or subfield (which area is this reseach taking place in? Including a difinition of the research area. minimum of 100 words)
        
        2. Themes & Subtopics: Extract a list of Themes or subtopics found in the document these themes should be based on the different subject and content and topics the document covers, str type(just the number) listing all the pages that topic shows up (e.g "1, 4, 16)
        
        3. Document Development: Extract ATLEAST ONE of the following (ALL If prominent):
           - Chronological Development (how the research has builds on previous work)
           - Theoretical Frameworks (the theories underpinning this research)
           - Methodological Approaches (detailed breakdown of methods explain in as much detail as possible. minimum of 300 words, the whole process)
        
        4. Methodological Information: (This is the most important part of the extraction, ensure to get as much detail as possible)
           - Study Design: (In as much detail as possible explaining the design of the study, You must walk the user through the design of the study in a way that they can implement it or easy to understand it, minimum of 200 words).
           - Participants: (Details about the participants, how they were selected, the number, and any other relevant information).
           - Data Collection: (Methods used to collect data, tools, and techniques  AND any other relevant information).
           - Data Analysis: (Approaches used to analyze data, transformation, statistical methods, and any other relevant information).
        
        5. Key Findings: List all the results, metics and findings. In a minimum of 300 words, Extract ALL the results from the study and key findings including the significance of each finding and any key quotes that support the findings. It is important to explain the meaning of the findings and how it came to be from the method.  List all the results,  minimum of 300 words
        
        6. Critical Analysis:
           - Method Strengths: list as many methodological strengths (2-5)
           - Method Limitations: list as many methodological limitations (2-5)
           - Result Strengths: list as many strengths of findings (2-5)
           - Result Weaknesses: list as many weaknesses of findings (2-5)
           - Potential Biases:  list as many potential biases or limitations 
        
        IMPORTANT INSTRUCTIONS:
        - Ensure to provide detailed information for each section as much as possible, You MUST ADHERE TO THE WORD COUNT FOR THE SECTION. Explain clarely in as much detail for the user to understand the whole research.
        - For each section, include PAGE NUMBER where the information was found. INT type(just the number)
        - For important statements, extract the EXACT TEXT and any CITATIONS in the text word for word
        - Must provide as must detail so the user have a clear understannding of the whole research.
        - Focus especially on detailed methodological information 
        - Maintain logical flow from methods to results/findings
        - Make complex methods, easy to understand walking though the steps for implementation
        \n\n
        
        # OUTPUT FORMAT: (For each section, provide as much detail as possible)
        Return a structured JSON object following this schema (example values shown):
        ```json
         {"""
                {
                "research_area": {
                    "description": "Identify the specific field or subfield of the research, including a definition of the research area. Explain in as much detail as possible.",
                    "page": "Page number where this information is found.INT type(just the number)"
                },
                "themes": [
                    {
                    "theme": "Exact a list of Themes or subtopics found in the document these themes should be based on the different subjects and topics the document covers",
                    "page": "Page number where this theme appears. str type(just the number) listing all the pages that topic shows up (e.g "1, 4, 16) "
                    }
                ],
                "chronological_development": {
                    "description": "Explanation of how the research builds on previous work, if present.",
                    "page": "Page number where this is discussed."
                },
                "theoretical_frameworks": {
                    "description": "Theoretical frameworks underpinning the research, if present.",
                    "page": "Page number where this is discussed."
                },
                "methodological_approaches": {
                    "study_design": {
                    "description": "Detailed explanation of the study design.",
                    "page": "Page number where this is discussed. INT type(just the number)"
                    },
                    "participants": {
                    "description": "Details about the participants, how they were selected, the number, and any other relevant information.",
                    "page": "Page number where this is discussed."
                    },
                    "data_collection": {
                    "description": "Methods used to collect data, including tools and techniques.",
                    "page": "Page number where this is discussed."
                    },
                    "data_analysis": {
                    "description": "Approaches used to analyze data, including statistical methods or transformations.",
                    "page": "Page number where this is discussed."
                    },
                    "key_quotes": [
                    {
                        "text": "Exact quote from the document relevant to methodology.",
                        "citation_data": "Citation information if available.",
                        "page": "Page number where the quote appears."
                    }
                    ]
                },
                "key_findings": [
                    {
                    "description": "Detailed explanation of all the finding, metrics and results explain all the results and the key findings.",
                    "significance": "Why this finding is important/ relation to the method.",
                    "key_quotes": [
                        {
                        "text": "Exact quote supporting the finding.",
                        "citation_data": "Citation information if available.",
                        "page": "Page number where the quote appears. INT type(just the number)"
                        }
                    ],
                    "page": "Page number where this finding is discussed."
                    },
                    {
                    "description": "Detailed explanation of all the finding, metrics and results  explain all the results and the key findings.",
                    "significance": "Why this finding is important/ relation to the method.",
                    "key_quotes": [
                        {
                        "text": "Exact quote supporting the finding.",
                        "citation_data": "Citation information if available.",
                        "page": "Page number where the quote appears."
                        }
                    ],
                    "page": "Page number where this finding is discussed."
                    }
                ],
                "method_strengths": [
                    {
                    "description": "Detailed explanation of a methodological strength.",
                    "key_quotes": [
                        {
                        "text": "Exact quote supporting the strength.",
                        "citation_data": "Citation information if available.",
                        "page": "Page number where the quote appears."
                        }
                    ],
                    "page": "Page number where this is discussed."
                    }
                ],
                "method_limitations": [
                    {
                    "description": "Detailed explanation of a methodological limitation.",
                    "key_quotes": [
                        {
                        "text": "Exact quote supporting the limitation.",
                        "citation_data": "Citation information if available.",
                        "page": "Page number where the quote appears."
                        }
                    ],
                    "page": "Page number where this is discussed."
                    }
                ],
                "result_strengths": [
                    {
                    "description": "Explanation of a strength in the research results.",
                    "key_quotes": [
                        {
                        "text": "Exact quote supporting the result strength.",
                        "citation_data": "Citation information if available.",
                        "page": "Page number where the quote appears."
                        }
                    ],
                    "page": "Page number where this is discussed."
                    }
                ],
                "result_weaknesses": [
                    {
                    "description": "Explanation of a weakness in the research results.",
                    "key_quotes": [
                        {
                        "text": "Exact quote supporting the result weakness.",
                        "citation_data": "Citation information if available.",
                        "page": "Page number where the quote appears."
                        }
                    ],
                    "page": "Page number where this is discussed."
                    }
                ],
                "potential_biases": [
                    {
                    "description": "Explanation of potential biases or limitations in the study.",
                    "key_quotes": [
                        {
                        "text": "Exact quote supporting the bias/limitation.",
                        "citation_data": "Citation information if available.",
                        "page": "Page number where the quote appears."
                        }
                    ],
                    "page": "Page number where this is discussed."
                    }
                ]
                } \n\n
          
       1. Research Area: minimum of 100 words. Identify the specific field or subfield (which area is this reseach taking place in? Including a difinition of the research area. minimum of 100 words)
        
        2. Themes & Subtopics: Extract a list of Themes or subtopics found in the document these themes should be based on the different subject and content the document covers, listing all the pages that topic shows up (e.g "1, 4, 16)
        
        3. Document Development: Extract ATLEAST ONE of the following (ALL If prominent):
           - Chronological Development (how the research has builds on previous work)
           - Theoretical Frameworks (the theories underpinning this research)
           - Methodological Approaches (detailed breakdown of methods explain in as much detail as possible. minimum of 300 words, the whole process)
        
        4. Methodological Information: (This is the most important part of the extraction, ensure to get as much detail as possible)
           - Study Design: (In as much detail as possible explaining the design of the study, You must walk the user through the design of the study in a way that they can implement it or easy to understand it, minimum of 200 words).
           - Participants: (Details about the participants, how they were selected, the number, and any other relevant information).
           - Data Collection: (Methods used to collect data, tools, and techniques  AND any other relevant information).
           - Data Analysis: (Approaches used to analyze data, transformation, statistical methods, and any other relevant information).
        
        5. Key Findings: List all the results, metics and findings. In a minimum of 300 words, Extract ALL the results from the study and key findings including the significance of each finding and any key quotes that support the findings. It is important to explain the meaning of the findings and how it came to be from the method.  List all the results,  minimum of 300 words
        
        6. Critical Analysis:
           - Method Strengths: list as many methodological strengths (2-5)
           - Method Limitations: list as many methodological limitations (2-5)
           - Result Strengths: list as many strengths of findings (2-5)
           - Result Weaknesses: list as many weaknesses of findings (2-5)
           - Potential Biases:  list as many potential biases or limitations \n
        
          
          
        IMPORTANT: You MUST ADHERE TO THE WORD COUNT FOR THE SECTION. Ensure to provide detailed information for each section as much  as possible, explain clarely in as much detail for the user to understand the whole research.

        """}
        ```
        """
        
        print(f"[LiteratureExtractor] Prompt constructed with length: {len(prompt)}")
        return prompt

    def _append_sections_with_page_markers(self, sections: List) -> str:
        """Combine document sections with clear page markers"""
        combined_text = ""
        
        for section in sections:
            # Access attributes directly on the model instance
            page_num = section.section_start_page_number
            content = section.content
            
            if content:
                combined_text += f"\n\n--- START PAGE {page_num} ---\n\n{content} \n\n--- END PAGE {page_num} ---\n\n"
        
        return combined_text

    def _extract_citations(self, text: str, reference_data: Dict[str, Any]) -> Dict:
        """Extract citations from text using the same approach as document_searcher"""
        try:
            # Use the existing citation extraction pattern
            cleaned_text = re.sub(r'\s+', ' ', text).strip()
            
            # First handle numbered citations
            citation_data = None
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
                
                # Match references
                if reference_data and 'entries' in reference_data:
                    for ref_num in ref_numbers:
                        if ref_num in reference_data['entries']:
                            citation_data['references'].append(
                                reference_data['entries'][ref_num]
                            )
                break  # Just get the first citation for now
                
            return citation_data
        except Exception as e:
            print(f"[LiteratureExtractor] Citation extraction error: {str(e)}")
            return None


    def call_openai_with_retry(self, model, messages, max_retries=3):
            """Call OpenAI API with retry logic and exponential backoff"""
            retry_count = 0
            base_wait_time = 1  # Start with 1 second
            
            while retry_count < max_retries:
                try:
                    response = self.llm.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=4000
                    )
                    return response
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str:  # Rate limit error
                        retry_count += 1
                        wait_time = base_wait_time * (2 ** retry_count)  # Exponential backoff
                        print(f"[LiteratureExtractor] Rate limit hit. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        
                        # If this is the last retry for the current model, log the error details
                        if retry_count == max_retries:
                            print(f"[LiteratureExtractor] Rate limit error details: {error_str}")
                    else:
                        # For other errors, raise immediately
                        raise
            
            # If we've exhausted retries
            raise Exception(f"Maximum retries exceeded when calling OpenAI API with model {model}")

    def extract_with_model(self, document_id, sections, reference_data, model_name):
        """Extract literature review data using a specific model"""
        print(f"[LiteratureExtractor] Attempting extraction with model: {model_name}")
        
        try:
            # Combine all sections with page markers
            combined_text = self._append_sections_with_page_markers(sections)
            
            # Prepare extraction prompt
            prompt = self._construct_extraction_prompt(combined_text)
            
            # Call OpenAI API with retry logic
            start_time = time.time()
            print(f"[LiteratureExtractor] Calling OpenAI API with model {model_name}")
            
            response = self.call_openai_with_retry(
                model=model_name,
                messages=[{
                    "role": "system",
                    "content": prompt
                }]
            )
            
            print(f"[LiteratureExtractor] API call with {model_name} completed")
            
            # Update token usage tracking
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            self.total_tokens_used += total_tokens
            self.total_api_calls += 1
            
            print(f"[LiteratureExtractor] Tokens used: {total_tokens} with model {model_name}")
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from content (in case there's additional text)
            try:
                json_content = content
                if "```json" in content:
                    json_content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_content = content.split("```")[1].split("```")[0].strip()
                
                extracted_data = json.loads(json_content)
                print("[LiteratureExtractor] Successfully parsed JSON response")
                
                # Post-process to add citation data
                if 'methodological_approaches' in extracted_data and 'key_quotes' in extracted_data['methodological_approaches']:
                    for quote in extracted_data['methodological_approaches']['key_quotes']:
                        if 'text' in quote and not quote.get('citation_data'):
                            quote['citation_data'] = self._extract_citations(quote['text'], reference_data)
                
                if 'key_findings' in extracted_data:
                    for finding in extracted_data['key_findings']:
                        if 'key_quotes' in finding:
                            for quote in finding['key_quotes']:
                                if 'text' in quote and not quote.get('citation_data'):
                                    quote['citation_data'] = self._extract_citations(quote['text'], reference_data)
                
                # Process other sections with key_quotes similarly
                
                duration = time.time() - start_time
                print(f"[LiteratureExtractor] Extraction completed in {duration:.2f}s with model {model_name}")
                
                return {
                    'document_id': document_id,
                    'extraction_data': extracted_data,
                    'processing_time': duration,
                    'model_used': model_name,
                    'status': 'success'
                }
                
            except json.JSONDecodeError as e:
                print(f"[LiteratureExtractor] JSON parsing error: {str(e)}")
                print(f"[LiteratureExtractor] Raw content: {content[:500]}...")
                raise Exception(f"Failed to parse literature review data from {model_name} response")
                
        except Exception as e:
            print(f"[LiteratureExtractor] Extraction error with model {model_name}: {str(e)}")
            raise

    def extract_literature_review(self, document_id: str, sections: List, reference_data: Dict) -> Dict:
        """Extract structured literature review data from document sections"""
        print(f"[LiteratureExtractor] Starting extraction for document: {document_id}")
        
        try:
            # Combine all sections to determine total size
            combined_text = self._append_sections_with_page_markers(sections)
            print(f"[LiteratureExtractor] Combined text length: {len(combined_text)}")
            
            # Select appropriate model
            selected_model = self.select_appropriate_model(len(combined_text))
            
            if not selected_model:
                print("[LiteratureExtractor] Document too large for any available model")
                return {
                    'document_id': document_id,
                    'status': 'error',
                    'error_message': 'Document is too large to process with available models. Please try a smaller document or split this document into smaller sections.'
                }
            
            # Try with selected model first
            try:
                return self.extract_with_model(document_id, sections, reference_data, selected_model)
            except Exception as e:
                print(f"[LiteratureExtractor] First attempt failed with model {selected_model}: {str(e)}")
                
                # If first model fails and it was the primary model, try fallback model
                if selected_model == self.PRIMARY_MODEL and self.FALLBACK_MODELS:
                    fallback_model = self.FALLBACK_MODELS[0]
                    print(f"[LiteratureExtractor] Trying fallback model: {fallback_model}")
                    
                    try:
                        return self.extract_with_model(document_id, sections, reference_data, fallback_model)
                    except Exception as fallback_error:
                        print(f"[LiteratureExtractor] Fallback model failed: {str(fallback_error)}")
                
                # If we get here, both models failed or there was no fallback
                return {
                    'document_id': document_id,
                    'status': 'error',
                    'error_message': f'Unable to extract literature review: {str(e)}'
                }
                
        except Exception as e:
            print(f"[LiteratureExtractor] Extraction error: {str(e)}")
            return {
                'document_id': document_id,
                'status': 'error',
                'error_message': str(e)
            }





















