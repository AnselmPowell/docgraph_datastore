# src/research_assistant/services/document_processor.py

from typing import Dict, List, Tuple, Any, Optional, NamedTuple
import time
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import re
from pathlib import Path
import os
import requests
from io import BytesIO
import uuid
import pandas as pd
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import (
    Title, NarrativeText, ListItem, Table, Image as UnstructuredImage
)

from django.conf import settings
from research_assistant.models import DocumentSection

from .cache_manager import DocumentCacheManager

# Update citation patterns
CITATION_PATTERNS = [
    # Existing patterns
    r'\(([^)]+?\d{4}[^)]+?)\)',  # Standard (Author, 2024)
    r'\((?:[A-Za-z]+, \d{4}|[A-Za-z]+ et al\., \d{4})\)',  # Complex citations
    
    # Add new patterns
    r'\[(\d+(?:,\s*\d+)*)\]',  # [1] or [1,2] or [1, 2, 3]
    r'\[(\d+)-(\d+)\]',  # [1-3]
    r'(?<![\w\d])\[(\d+)\](?![\w\d])',  # Standalone [1]
]


# Reference section markers
REFERENCE_SECTION_TITLES = [
    # Basic variations
    r'^\s*references?\s*$',
    r'^\s*bibliography\s*$', 
    r'^\s*works\s+cited\s*$',
    r'^\s*reference\s+list\s*$',
    r'^\s*literature\s+cited\s*$',
    
    # Numbered variations
    r'^\s*(?:\d+\.|[ivx]+\.|\[\d+\])\s*references?\s*$',
    
    # With decorators
    r'^[-_*=]{2,}\s*references?\s*[-_*=]{2,}$',
    r'^\s*references?\s*[-_*=]{2,}$',
    r'^[-_*=]{2,}\s*references?\s*$'
]

# Reference entry patterns
REFERENCE_ENTRY_PATTERNS = {
    'numbered_bracket(3)': r'^\s*\[(\d+)\]\s*(.+)$',  # [1] Author...
    'numbered_bracket_arxiv': r'^\s*\[(\d+)\]\s*([\w\s,]+?)\.\s+arXiv preprint\s+arXiv:(\d+\.\d+)',
    'numbered_paren': r'^\s*\((\d+)\)\s*(.+)$',    # (1) Author...
    'numbered_dot': r'^\s*(\d+)\.\s*(.+)$',        # 1. Author...
    'numbered_parenthesis': r'\((\d+)\)\s+(.+)',
    'numbered_dot': r'(\d+)\.\s+(.+)',
    'author_year': r'^([A-Z][a-zA-Z\s,\.&]+)\s*\((\d{4})\)\s*(.+)$',  # Author (2024)...
    'apa_style': r'^([A-Z][a-zA-Z\s,\.&]+)\s*\((\d{4})\)\.\s*([^\.]+)\.',  # Author, A., & Author, B. (2024). Title...
    'mla_style': r'^([A-Z][a-zA-Z\s,\.]+)\.\s*"([^"]+)"\s*(.+),\s*(\d{4})\.',  # Author. "Title," Journal, Year.
    'footnote_numbered': r'^\s*(\d+)\.\s*([A-Z].+?)\s*"([^"]+)",\s*(.+),\s*(\d{4})', # 1. Author, "Title," Journal, Year.
    # Matches [159] format (numeric citation with square brackets)
    'numbered_bracket': r"^\[(\d+)\]\s+([A-Za-z\s,]+)\.\s*(\d{4})\.\s*([\w\s-]+)\.\s*([\w\s-]+)?",

    # Matches numbered references with period (e.g., 159.)
    'numbered_period': r"^(\d+)\.\s+([A-Za-z\s,]+)\.\s*(\d{4})\.\s*([\w\s-]+)\.\s*([\w\s-]+)?",

    # Matches numbered references with parenthesis (e.g., 159) Wang et al., 2023)
    'numbered_parenthesis': r"^(\d+)\)\s+([A-Za-z\s,]+)\.\s*(\d{4})\.\s*([\w\s-]+)\.\s*([\w\s-]+)?",

    # Matches parenthetical in-line citations (e.g., (Wang et al., 2023))
    'inline_citation': r"\(([\w\s]+? et al\.),\s*(\d{4})\)",

    # General fallback for text with author, year, title (more flexible)
    'general_fallback': r"([A-Za-z\s,]+)\.\s*(\d{4})\.\s*([\w\s,]+?)\.?\s*([\w\s]+)?",

    # Match references with "et al." (multiple authors listed in abbreviated form)
    'et_al_format': r"^([A-Za-z\s,]+) et al\.\s*(\d{4})\.\s*([\w\s-]+)\.\s*([\w\s-]+)?",

    # Match references with multiple authors (no "et al."), e.g., "Wang, Li, Sun, and Liu. 2023."
    'multi_author': r"^([A-Za-z\s,]+(?:, [A-Za-z\s]+)*),\s*(\d{4})\.\s*([\w\s-]+)\.\s*([\w\s-]+)?",

    # Match DOI-based citations (common in academic papers)
    'doi_citation': r"^([A-Za-z\s,]+)\.\s*(\d{4})\.\s*([\w\s-]+)\.\s*doi:\s*(\S+)",

    # Match references with volume and issue numbers (e.g., Journal Name, Vol. 12, Issue 3)
    'journal_volume_issue': r"^([A-Za-z\s,]+)\.\s*(\d{4})\.\s*([\w\s-]+)\.\s*Vol\.\s*(\d+),\s*Issue\s*(\d+)",

    # Match references with page ranges (e.g., Pages 123–130)
    'page_range': r"^([A-Za-z\s,]+)\.\s*(\d{4})\.\s*([\w\s-]+)\.\s*Pages\s*(\d+\s*[-–]\s*\d+)",

    # Match references with journal or conference name (e.g., In Journal of AI Research)
    'journal_or_conference': r"^([A-Za-z\s,]+)\.\s*(\d{4})\.\s*([\w\s-]+)\.\s*In\s*([\w\s-]+)\s*(\d+)$",

    # Match references with "In Proceedings of" (e.g., In Proceedings of the 2023 NLP Conference)
    'proceedings_format': r"^([A-Za-z\s,]+)\.\s*(\d{4})\.\s*([\w\s-]+)\.\s*In\s*Proceedings\s*of\s*([\w\s-]+)",
    
    # Match references with URL links (e.g., Website or Online articles)
    'url_reference': r"^([A-Za-z\s,]+)\.\s*(\d{4})\.\s*([\w\s-]+)\.\s*Retrieved\s*from\s*(https?://[\S]+)",

    # Match references with corporate authors (e.g., World Health Organization, 2023)
    'corporate_author': r"^([A-Za-z\s]+),\s*(\d{4})\.\s*([\w\s-]+)\.\s*([\w\s]+)?",

    # Match book references with title, publisher, and year (e.g., Author Name. Title of the Book. Publisher, Year.)
    'book_reference': r"^([A-Za-z\s,]+)\.\s*([\w\s-]+)\.\s*([\w\s-]+)\.\s*(\d{4})$",

    # Match references with multiple books (e.g., Author1, Author2, Author3. Book1, Book2. Year.)
    'multi_book_reference': r"^([A-Za-z\s,]+)\.\s*([\w\s,]+)\.\s*(\d{4})$",
}




IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}

class TitleGroup:
    """Manages elements belonging to a title section"""
    def __init__(self, title_element, group_number: int):
        self.title = title_element
        self.group_number = group_number
        self.elements = []
        self.sections = []
        
        # Safely handle metadata access
        if title_element:
            title_dict = title_element.to_dict()
            self.start_page = (
                title_dict.get('metadata', {}).get('page_number', 1)
                if title_dict and 'metadata' in title_dict
                else 1
            )
        else:
            self.start_page = 1
        
    def add_element(self, element):
        self.elements.append(element)
        
    def get_title_text(self):
        # Safely handle title text access
        if self.title:
            title_dict = self.title.to_dict()
            return title_dict.get('text', '')
        return ''
    
    def __str__(self):
        title_preview = self.get_title_text()[:30] if self.get_title_text() else 'No Title'
        return f"TitleGroup {self.group_number}: {title_preview}..."

class Section:
    """Represents a processed document section"""
    def __init__(
        self,
        elements: List[Any],
        section_type: str,
        position: int,
        title_group: TitleGroup,
        page_number: int,
        document_id: str,
    ):
        self.elements = elements
        self.type = section_type
        self.position = position
        self.title_group = title_group
        self.page_number = page_number
        self.document_id = document_id
        self.section_id = f"{document_id}_p{page_number}_{section_type}_{uuid.uuid4().hex[:8]}"
        self.prev_section = None
        self.next_section = None
        
    def get_combined_text(self) -> str:
        """Combines text from all elements"""
        return '\n'.join(el.text for el in self.elements if hasattr(el, 'text'))
    
    def get_context_text(self) -> Tuple[Optional[str], Optional[str]]:
        """Gets context from adjacent sections"""
        prev_text = self.prev_section.elements[-1].text if self.prev_section and self.prev_section.elements else None
        next_text = self.next_section.elements[0].text if self.next_section and self.next_section.elements else None
        return prev_text, next_text

class DocumentProcessor:
    """Enhanced document processor with title-based chunking and section organization"""
    
    def __init__(self, document_id: str = None, document_url: str = None):
        print("\n[DocumentProcessor] Initializing document processor")
        self.document_id = document_id or str(uuid.uuid4())
        self.document_url = document_url
        self.data_dir = Path("research_assistant/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.title_groups = []
        self.sections = []

        self.cache_manager = DocumentCacheManager()
        
        print(f"[DocumentProcessor] Initialized for document {self.document_id}")
        print(f"[DocumentProcessor] Document URL: {document_url}")
        print(f"[DocumentProcessor] Data directory: {self.data_dir}")
        

    def _download_file(self, url: str) -> str:
        """Download file from URL with enhanced monitoring"""
        print(f"[DocumentProcessor] Starting file download: {url}")
        
        start_time = time.time()
        response = requests.get(url, timeout=30)
        
        print(f"[DocumentProcessor] Download status: {response.status_code}")
        print(f"[DocumentProcessor] Content type: {response.headers.get('content-type')}")
        
        file_path = self.data_dir / f"temp_{self.document_id}.pdf"
        with open(file_path, 'wb') as f:
            content = response.content
            f.write(content)
        
        download_time = time.time() - start_time
        file_size = len(content)
        
        print(f"[DocumentProcessor] File downloaded: {file_path}")
        print(f"[DocumentProcessor] Size: {file_size / 1024:.2f} KB")
        print(f"[DocumentProcessor] Time: {download_time:.2f}s")
        
        
        return str(file_path)

    def _extract_reference_section(self, elements: List[Any]) -> Tuple[List[Any], Dict[str, Any]]:
        """Extract reference section with comprehensive text analysis"""
        print("\n[DocumentProcessor] Starting reference section extraction")
        print(f"[DocumentProcessor] Total elements to process: {len(elements)}")
        
        def is_reference_header(idx: int, text: str) -> bool:
            """Check if text contains a reference section header"""
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                cleaned_line = re.sub(r'[-_*=\[\]()]', '', line).strip()
                
                if cleaned_line.lower() == 'references':
                    print(f"[DocumentProcessor] Found reference header: 'references'")
                    return True
                    
                # Check for numbered variations
                if re.search(r'references?', cleaned_line, re.IGNORECASE):
                    if re.match(r'.*\d+.*', line):
                        print(f"[DocumentProcessor] Found numbered reference header: {line}")
                        return True
            
            return False

        def extract_single_reference(text: str) -> Optional[Dict]:
            """Extract a single reference entry"""
            text = text.strip()
            print(f"\n[DocumentProcessor] Processing reference text: {text[:100]}...")

            # Skip empty lines or section headers
            if not text or text.upper() == 'REFERENCES':
                print("[DocumentProcessor] Skipping empty line or header")
                return None

            # Match [number] pattern
            ref_match = re.match(r'^\[(\d+)\](.*)', text)
            if not ref_match:
                print("[DocumentProcessor] No reference number found")
                return None

            ref_number = ref_match.group(1)
            ref_text = ref_match.group(2).strip()
            
            print(f"[DocumentProcessor] Extracted reference #{ref_number}")
            print(f"[DocumentProcessor] Reference text: {ref_text[:100]}...")

            return {
                'id': ref_number,
                'text': ref_text,
                'type': 'numbered'
            }

        # Initialize reference data
        reference_data = {
            'entries': {},
            'type': 'unknown',
            'start_page': None,
            'end_page': None,
            'start_index': None,
            'end_index': None
        }
        
        # Find reference section
        ref_start_idx = None
        print("\n[DocumentProcessor] Searching for reference section...")
        
        for idx in range(len(elements)-1, -1, -1):
            element = elements[idx]
            element_dict = element.to_dict()
            text = element_dict.get('text', '').strip()
            
            if text and is_reference_header(idx, text):
                print(f"[DocumentProcessor] Found reference section at index {idx}")
                ref_start_idx = idx
                reference_data['start_page'] = element_dict.get('metadata', {}).get('page_number', 1)
                reference_data['type'] = text
                break
        
        if ref_start_idx is not None:
            print("\n[DocumentProcessor] Processing reference section...")
            
            # Get all text after references header
            reference_text = ' '.join(
                element.to_dict().get('text', '').strip()
                for element in elements[ref_start_idx:]
            )
            
            print("\n[DocumentProcessor] Extracted reference text:")
            print("-" * 50)
            print(reference_text[:500] + "...")
            print("-" * 50)
            
            # Find all references using regex
            print("\n[DocumentProcessor] Finding all references...")
            references = re.finditer(r'\[(\d+)\](.*?)(?=\[\d+\]|$)', reference_text, re.DOTALL)
            
            ref_count = 0
            for match in references:
                ref_number = match.group(1)
                ref_text = match.group(2).strip()
                
                print(f"\n[DocumentProcessor] Found reference #{ref_number}")
                print(f"[DocumentProcessor] Text: {ref_text[:100]}...")
                
                reference_data['entries'][ref_number] = {
                    'text': ref_text,
                    'type': 'numbered'
                }
                ref_count += 1
            
            print(f"\n[DocumentProcessor] Successfully extracted {ref_count} references")
            
            # Set section boundaries
            reference_data['start_index'] = ref_start_idx
            reference_data['end_index'] = len(elements)
        
        # Print summary
        print("\n[DocumentProcessor] Reference extraction summary:")
        print(f"- Found {len(reference_data['entries'])} references")
        print(f"- Section starts on page {reference_data['start_page']}")
        print(f"- Section starts at index {reference_data['start_index']}")
        
        return [], reference_data


    def _extract_citations(self, text: str, reference_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced citation extraction with reference matching"""
        print("\n" + "="*50)
        print("[Citation Extraction] Starting citation extraction process")
        print(f"[Citation Extraction] Text length: {len(text)}")
        
        # Clean the input text first
        cleaned_text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
        print("\n[Text Processing] Cleaned text sample:")
        print(f"'{cleaned_text[:100]}...'")
        print("="*50 + "\n")

        citations = []
        
        try:
            print("[Citation Extraction] Processing citation patterns:")
            for pattern in CITATION_PATTERNS:
                print(f"\n[Pattern Analysis] Checking pattern: {pattern}")
                matches = re.finditer(pattern, cleaned_text)
                
                for match in matches:
                    try:
                        citation_text = match.group(0)
                        print(f"\n  [Found Citation] Raw text: '{citation_text}'")
                        print(f"  [Found Citation] Position: {match.span()}")
                        
                        # Basic validation of citation text
                        if not citation_text or len(citation_text) > 100:  # Skip invalid citations
                            print("  [Validation] Skipping invalid citation")
                            continue

                        citation_data = {
                            'text': citation_text,
                            'type': 'unknown',
                            'references': [],
                            'position': match.span(),
                            'source': 'text'  # Default source
                        }

                        # Detect citation source (table, figure, or text)
                        context_before = cleaned_text[max(0, match.start() - 50):match.start()]
                        if any(marker in context_before.lower() for marker in ['table', 'fig', 'figure']):
                            citation_data['source'] = 'figure/table'
                            print("  [Context] Citation found in figure/table")

                        # Handle different citation types
                        if citation_text.startswith('['):
                            print("  [Citation Type] Detected numbered citation")
                            citation_data['type'] = 'numbered'
                            
                            # Extract numbers, handle both [1] and [1,2,3] formats
                            numbers = re.findall(r'\d+', citation_text)
                            print(f"  [Number Extraction] Found numbers: {numbers}")

                            for num in numbers:
                                print(f"  [Reference Lookup] Checking reference #{num}")
                                if ref_text := reference_data['entries'].get(num):
                                    print(f"  [Reference Match] Found matching reference for #{num}")
                                    citation_data['references'].append({
                                        'id': num,
                                        'text': ref_text
                                    })
                                else:
                                    print(f"  [Reference Lookup] No matching reference found for #{num}")

                        else:
                            print("  [Citation Type] Checking for author-year format")
                            # Enhanced author-year pattern to handle various formats
                            author_year_match = re.search(r'(?:\()?([A-Za-z]+)(?:,|\s+et\s+al\.?)?\s*[,\s]\s*(\d{4})(?:\))?', citation_text)
                            
                            if author_year_match:
                                author = author_year_match.group(1).strip()
                                year = author_year_match.group(2)
                                print(f"  [Author-Year] Extracted: Author='{author}', Year='{year}'")
                                
                                citation_data['type'] = 'author_year'
                                ref_id = f"{author}_{year}"
                                
                                if ref_text := reference_data['entries'].get(ref_id):
                                    print(f"  [Reference Match] Found matching reference")
                                    citation_data['references'].append({
                                        'id': ref_id,
                                        'text': ref_text
                                    })
                                else:
                                    print(f"  [Reference Lookup] No matching reference found for {ref_id}")

                        citations.append(citation_data)
                        print(f"  [Processing] Added citation to list (Total: {len(citations)})")

                    except Exception as e:
                        print(f"  [Warning] Error processing individual citation: {str(e)}")
                        continue

            print("\n" + "="*50)
            print("[Citation Summary]")
            print(f"Total citations found: {len(citations)}")
            for idx, citation in enumerate(citations, 1):
                print(f"\nCitation #{idx}:")
                print(f"- Text: '{citation['text']}'")
                print(f"- Type: {citation['type']}")
                print(f"- Source: {citation['source']}")
                print(f"- References matched: {len(citation['references'])}")
            print("="*50)

        except Exception as e:
            print(f"[Error] Fatal error in citation extraction: {str(e)}")
            print(f"[Error] Returning empty citations list")
            return []

        return citations
    
    def _determine_element_type(self, element: Any) -> str:
        """Determine element type with monitoring"""
        print("\n[DocumentProcessor] Determining element type")
        
        try:
            element_dict = element.to_dict()
            raw_type = element_dict.get('type', '')
            
            # Map unstructured types to our types
            element_type = "text"  # default type
            
            if raw_type == 'Title':
                element_type = "title"
            elif raw_type == 'Table':
                element_type = "table"
            elif raw_type == 'Image':
                element_type = "image"
            elif raw_type == 'List' or raw_type == 'ListItem':
                element_type = "list"
            elif raw_type == 'Formula':
                element_type = "formula"
            elif raw_type == 'CompositeElement':
                # For composite elements, try to determine type from content
                if any(marker in str(element_dict.get('text', '')).lower() 
                    for marker in ['figure', 'fig.', 'fig ']):
                    element_type = "figure"
                elif any(marker in str(element_dict.get('text', '')).lower() 
                        for marker in ['table', 'tbl.', 'tbl ']):
                    element_type = "table"
            
            print(f"[DocumentProcessor] Raw type: {raw_type}")
            print(f"[DocumentProcessor] Mapped to element type: {element_type}")
            
            return element_type
            
        except Exception as e:
            print(f"[DocumentProcessor] Error determining element type: {str(e)}")
            # Return default type on error
            return "text"

    def _organize_title_groups(self, elements: List[Any]) -> List[TitleGroup]:
        """Organize elements into title groups"""
        print("\n[DocumentProcessor] Organizing elements into title groups")
        
        title_groups = []
        current_group = None
        group_number = 0
        
        # Debug initial elements
        print(f"[DocumentProcessor] Total elements to process: {len(elements)}")
        if elements and len(elements) > 0:
            element_dict = elements[0].to_dict()
            print(f"[DocumentProcessor] First element type: {element_dict.get('type')}")
        
        for element in elements:
            try:
                element_dict = element.to_dict()
                element_type = element_dict.get('type', '')
                
                # Check if this is a title element
                if element_type == 'Title':  # Changed from isinstance check to type string check
                    group_number += 1
                    print(f"[DocumentProcessor] Processing title group {group_number}")
                    current_group = TitleGroup(element, group_number)
                    title_groups.append(current_group)
                    print(f"[DocumentProcessor] Created new title group: {current_group}")
                elif current_group:
                    current_group.add_element(element)
                else:
                    # Handle elements before first title
                    if not title_groups:
                        group_number += 1
                        print(f"[DocumentProcessor] Creating initial group for elements before first title")
                        current_group = TitleGroup(None, group_number)
                        title_groups.append(current_group)
                    current_group.add_element(element)
                    
            except Exception as e:
                print(f"[DocumentProcessor] Warning: Error processing element {element}: {str(e)}")
                continue
        
        print(f"[DocumentProcessor] Created {len(title_groups)} title groups")
        for idx, group in enumerate(title_groups, 1):
            print(f"[DocumentProcessor] Group {idx} has {len(group.elements)} elements")
        
        return title_groups

    def _create_sections_from_title_group(self, title_group: TitleGroup) -> List[Section]:
        """Create sections from elements in a title group"""
        print(f"\n[DocumentProcessor] Creating sections for {title_group}")
        
        sections = []
        text_elements = []
        current_position = len(self.sections)
        
        for element in title_group.elements:
            element_type = self._determine_element_type(element)
            
            if element_type in ['image', 'table', 'diagram']:
                # Process pending text elements
                if text_elements:
                    sections.extend(self._create_text_sections(
                        text_elements, 
                        current_position + len(sections),
                        title_group
                    ))
                    text_elements = []
                
                # Create section for non-text element
                sections.append(Section(
                    elements=[element],
                    section_type=element_type,
                    position=current_position + len(sections),
                    title_group=title_group,
                    page_number=element.metadata.page_number if hasattr(element.metadata, 'page_number') else 1,
                    document_id=self.document_id
                ))
            else:
                text_elements.append(element)
        
        # Process any remaining text elements
        if text_elements:
            sections.extend(self._create_text_sections(
                text_elements,
                current_position + len(sections),
                title_group
            ))
        
        print(f"[DocumentProcessor] Created {len(sections)} sections for title group")
        return sections

    def _create_text_sections(
        self, 
        elements: List[Any], 
        start_position: int,
        title_group: TitleGroup
    ) -> List[Section]:
        """Create sections from text elements"""
        print(f"\n[DocumentProcessor] Creating text sections from {len(elements)} elements")
        
        sections = []
        i = 0
        
        while i < len(elements):
            remaining = len(elements) - i
            
            if remaining >= 3:
                # Create section with 3 elements
                sections.append(Section(
                    elements=elements[i:i+3],
                    section_type='text',
                    position=start_position + len(sections),
                    title_group=title_group,
                    page_number=elements[i].metadata.page_number if hasattr(elements[i].metadata, 'page_number') else 1,
                    document_id=self.document_id
                ))
                i += 3
            else:
                # Create section with remaining elements
                sections.append(Section(
                    elements=elements[i:i+remaining],
                    section_type='text',
                    position=start_position + len(sections),
                    title_group=title_group,
                    page_number=elements[i].metadata.page_number if hasattr(elements[i].metadata, 'page_number') else 1,
                    document_id=self.document_id
                ))
                i += remaining
        
        print(f"[DocumentProcessor] Created {len(sections)} text sections")
        return sections

    def _link_adjacent_sections(self):
        """Link adjacent text sections for context"""
        print("\n[DocumentProcessor] Linking adjacent text sections")
        
        text_sections = [s for s in self.sections if s.type == 'text']
        
        for i in range(len(text_sections)):
            if i > 0:
                text_sections[i].prev_section = text_sections[i-1]
            if i < len(text_sections) - 1:
                text_sections[i].next_section = text_sections[i+1]
        
        print(f"[DocumentProcessor] Linked {len(text_sections)} text sections")

    def _create_section_data(self, section: Section) -> Dict:
        """Create section data dictionary with citations and references"""
        section_data = {
            # Keep existing fields
            'document_id': section.document_id,
            'section_id': section.section_id,
            'section_type': section.type,
            'page_number': section.page_number,
            'position': section.position,
            'url': self.document_url,
            'pointer': {
                'page_number': section.page_number,
                'section_start': section.get_combined_text()[:15].ljust(15),
                'title_group_number': section.title_group.group_number,
                'title_text': section.title_group.get_title_text()
            },
            'content': {
                'text': section.get_combined_text(),
                'type': section.type,
                # Update citations to use new extraction
                'citations': []  # Will be filled by reference data
            },
            'metadata': {
                'element_details': {},
                'adjacent_sections': {},
                # Add new citation metadata
                'citations': {
                    'entries': [],
                    'count': 0,
                    'types': [],
                    'has_matches': False
                },
                # Add reference relationships
                'reference_data': {
                    'matches': [],
                    'section_type': 'content'  # or 'references' for reference section
                }
            }
        }
        
        # Add context information
        prev_text, next_text = section.get_context_text()
        if prev_text:
            section_data['metadata']['adjacent_sections']['previous'] = prev_text
        if next_text:
            section_data['metadata']['adjacent_sections']['next'] = next_text
                
        return section_data

    def process_document(self, file_path: str) -> List[Dict[str, Any]]:
        """Enhanced document processing with title-based chunking"""
        print(f"\n[DocumentProcessor] Starting document processing: {self.document_id}")
        
        start_time = time.time()



        # Convert PDF to images
        # print("[DocumentProcessor] Converting PDF to images")
        # page_images = convert_from_path(file_path, dpi=300)
        # print(f"[DocumentProcessor] Converted {len(page_images)} pages to images")
        
        # Parse PDF content
        print("[DocumentProcessor] Parsing PDF content")
        elements = partition_pdf(
            filename=file_path,
            strategy="hi_res",
            include_page_breaks=True,
            infer_table_structure=True,
            extract_image_block_types=['image'],
            extract_image_blocks_to_playload=True,
            chunking_strategy="by_title",
            max_characters=10000,
            combine_text_under_n_chars=2000,
            new_after_n_chars=6000,
        )
        
        print("[DocumentProcessor] Number of section elements: ", len(elements) )
            # Extract reference section first
        reference_data = self._extract_reference_section(elements)
        # print(f"STOP HERE")
        # print(f"[DocumentProcessor] {stop}")
        print(f"[DocumentProcessor] Extracted {len(elements)} elements")
        
        # Organize into title groups
        self.title_groups = self._organize_title_groups(elements)
        
        # Create sections from title groups
        for title_group in self.title_groups:
            new_sections = self._create_sections_from_title_group(title_group)
            self.sections.extend(new_sections)
            title_group.sections = new_sections
        
        # Link adjacent sections
        self._link_adjacent_sections()
        
        # Create final section data
        processed_sections = []
        for section in self.sections:
            section_data = self._create_section_data(section)
            processed_sections.append(section_data)

            # Add citations and references if this is a text section
            print("[DocumentProcessor] Processing section type: ", section.type)
            if section.type == 'text':
                citations = self._extract_citations(
                    section.get_combined_text(), 
                    reference_data
                )
                section_data['metadata']['citations']['entries'] = citations
                section_data['metadata']['citations']['count'] = len(citations)
                section_data['metadata']['citations']['types'] = list(set(c['type'] for c in citations))
                section_data['metadata']['citations']['has_matches'] = any(c['references'] for c in citations)
            
            processed_sections.append(section_data)
        
        processing_time = time.time() - start_time
        print(f"\n[DocumentProcessor] Processing completed:")
        print(f"  Title groups: {len(self.title_groups)}")
        print(f"  Total sections: {len(processed_sections)}")
        print(f"  Processing time: {processing_time:.2f}s")
        


        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[DocumentProcessor] Cleaned up temporary file: {file_path}")
        
        return processed_sections

    def process_document_from_url(self, url: str) -> List[Dict[str, Any]]:
        """Process document from URL"""
        print(f"\n[DocumentProcessor] Processing document from URL: {url}")

        # Check if document exists in cache/DB
        cached_data = self.cache_manager.get_document_data_sync(self.document_id)
        print(f"[DocumentProcessor] Cached data:{self.document_id} ------ {cached_data}")
        if cached_data:
            print("[DocumentProcessor] Using cached document data")
            # Important: Return the processed sections from the cache
            return cached_data.get('sections', [])

        print("[DocumentProcessor] No cache found, processing document")
        print(f"[DocumentProcessor] Starting URL processing")
        file_path = self._download_file(url)
        sections = self.process_document(file_path)
        print(f"[DocumentProcessor] Retrieved {len(sections)} sections")
        return sections
