
# src/research_assistant/services/document_processor.py



from .pdf_parser import PDFParser
from typing import Dict, List, Tuple, Any, Optional
import time
from datetime import datetime
import fitz  # PyMuPDF
from pathlib import Path
import os
import requests
from io import BytesIO
import uuid
import re
import json
import logging
from dataclasses import dataclass



from pdf2docx import Converter
import pdfplumber


# Reference section markers - keeping existing ones and adding new
REFERENCE_SECTION_TITLES = [
    r'^\s*references?\s*$',
    r'^\s*bibliography\s*$', 
    r'^\s*works\s+cited\s*$',
    r'^\s*reference\s+list\s*$',
    r'^\s*(?:\d+\.|[ivx]+\.|\[\d+\])\s*references?\s*$',
    r'^[-_*=]{2,}\s*references?\s*[-_*=]{2,}$',
    r'^\s*references?\s*[-_*=]{2,}$',
    r'^[-_*=]{2,}\s*references?\s*$',
    r'^\s*acknowledgements?\s*$',
]

# Reference section markers - keeping your existing ones
REFERENCE_SECTION_TITLES = [
    r'^\s*references?\s*$',
    r'^\s*bibliography\s*$', 
    r'^\s*works\s+cited\s*$',
    r'^\s*reference\s+list\s*$',
    r'^[-_*=]{2,}\s*references?\s*[-_*=]{2,}$',
    r'^\d+\.\s*references?\s*$'
]

# Define reference patterns
REFERENCE_PATTERNS = {
    'numbered_bracket': r'^\s*\[(\d+)\]',           # [1]
    'numbered_dot': r'^\s*(\d+)\.',                 # 1.
    'author_year': r'^\s*\[([A-Za-z]+(?:\s*,\s*[A-Za-z]+)*\s*\(\d{4}[a-z]?\))\]',  # [Author(2023a)]
    'parenthetical': r'^\s*\(([A-Za-z]+\s*,\s*\d{4})\)',  # (john,2024)
    'narrative': r'^([A-Za-z]+\s+et\s+al\.\s*\(\d{4}\))',  # AuthorName et al.(2016)
    'standard': r'^([A-Za-z]+\s*,\s*[A-Za-z]+\s*\.\s*\d{4})'  # Ammann P., Offutt.J. 2008
}

# In-text citation patterns
CITATION_PATTERNS = {
    'numbered': r'\[(\d+(?:,\s*\d+)*)\]',          # [1] or [1,2,3]
    'parenthetical': r'\(([A-Za-z]+\s+et\s+al\.,\s*\d{4})\)',  # (Kim et al., 2016)
    'narrative': r'([A-Za-z]+\s+et\s+al\.\s*\(\d{4}\))',  # Author et al. (2023)
    'with_page': r'\(([A-Za-z]+,\s*\d{4},\s*p\.\s*\d+)\)',  # (Smith, 2020, p.45)
    'author_year': r'\(([A-Za-z]+,\s*[A-Za-z]\.,\s*\d{4}(?:-\d{4})?\.?)\)'  # (Tatham, S., 2001-2015.)
}




# Custom types
@dataclass
class ImageMetadata:
    """Data class for storing image metadata"""
    filename: str
    path: str
    extraction_date: str
    page_number: int
    image_index: int
    width: int = None
    height: int = None

class Section:
    """Represents a processed document section (page)"""
    def __init__(
        self,
        text: str,
        section_type: str,
        section_start_page_number: int,
        document_id: str,
        prev_page_text: Optional[str] = None,
        next_page_text: Optional[str] = None,
        tables: Optional[List[List[List[str]]]] = None,
        images: Optional[List[ImageMetadata]] = None
    ):
        self.text = text
        self.type = section_type
        self.section_start_page_number = section_start_page_number
        self.document_id = document_id
        self.section_id = f"{document_id}_p{section_start_page_number}_{uuid.uuid4().hex[:8]}"
        self.prev_page_text = prev_page_text
        self.next_page_text = next_page_text
        self.tables = tables or []
        self.images = images or []

    def get_context_text(self, window_size: int = 0) -> str:
        """Gets context from adjacent pages with specified word window"""
        context = []
        if self.prev_page_text:
            prev_words = self.prev_page_text.split()[-window_size:]
            context.append(' '.join(prev_words))
            
        context.append(self.text)
        
        if self.next_page_text:
            next_words = self.next_page_text.split()[:window_size]
            context.append(' '.join(next_words))
            
        # return '\n'.join(context)
        return self.text

class DocumentProcessor:
    """Enhanced document processor with custom PDF parsing"""
    
    def __init__(self, document_id: str = None, document_url: str = None):
        """Initialize document processor
        
        Input:
            document_id: Optional[str] - Unique document identifier
            document_url: Optional[str] - URL to PDF document
            
        Output: None
        
        Creates processing pipeline with:
        - document_id: str
        - document_url: str  
        - data_dir: Path
        - sections: List[Section]
        """
        print("\n[DocumentProcessor] Initializing document processor")
        self.document_id = document_id
        self.document_url = document_url
        self.data_dir = Path("research_assistant/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sections = [],
        self.total_pages = 0,
        self.reference_data ={}
        
        print(f"[DocumentProcessor] Initialized for document {self.document_id}")
        print(f"[DocumentProcessor] Document URL: {document_url}")
        print(f"[DocumentProcessor] Data directory: {self.data_dir}")

    def _download_file(self, url: str) -> str:
        """Download file from URL
        
        Input:
            url: str - URL to download PDF from
            
        Output:
            str - Local file path to downloaded PDF
            
        Side effects:
            - Creates temporary file in self.data_dir
        """
        print(f"[DocumentProcessor] Starting file download: {url}")
        
        response = requests.get(url, timeout=30)
        
        print(f"[DocumentProcessor] Download status: {response.status_code}")
        print(f"[DocumentProcessor] Content type: {response.headers.get('content-type')}")
        
        file_path = self.data_dir / f"temp_{self.document_id}.pdf"
        with open(file_path, 'wb') as f:
            content = response.content
            f.write(content)
        
        print(f"[DocumentProcessor] File downloaded: {file_path}")
        
        return str(file_path)

    def _cleanup_temp_file(self, file_path):
        """Delete temporary PDF file."""
        try:
            Path(file_path).unlink()
            print(f"[DocumentProcessor] Temporary file deleted: {file_path}")
        except Exception as e:
            print(f"[DocumentProcessor] Error deleting temporary file: {e}")

    

    def get_total_pages(self):
        print("Get total number of Pages:", self.total_pages)
        return self.total_pages

    def process_document_from_url(self, url: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Process document from URL
        
        Input:
            url: str - URL to PDF document
            
        Output: 
            Tuple[List[Dict], Dict]:
            - List of section data dictionaries
            - Reference data dictionary
            
        Section data format:
        {
            'document_id': str,
            'section_id': str,
            'section_type': str,
            'section_start_page_number': int,
            'content': {
                'text': str,
                'type': str,
                'has_citations': bool
            },
            'citations': List[Dict],
            'reference_data': Dict
        }
        """
        print(f"\n[DocumentProcessor] Processing document from URL: {url}")
        print(f"[DocumentProcessor] Starting URL processing")
        file_path = self._download_file(url)
        sections, reference_data = self.process_document(file_path)
        self._cleanup_temp_file(file_path)
        print(f"[DocumentProcessor] Retrieved {len(sections)} sections")


        return sections, reference_data

    def process_document(self, file_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Process PDF document to extract content and structure
        
        Input:
            file_path: str - Path to PDF file
            
        Output:
            Tuple[List[Dict], Dict]:
            - List of section data (one per page)
            - Reference data dictionary
            
        Processing steps:
        1. Parse PDF with custom parser
        2. Extract references
        3. Create sections with page overlays
        4. Process citations
        """
        print(f"\n[DocumentProcessor] Starting document processing: {self.document_id}")
        
        start_time = time.time()
        
        # Initialize custom PDF parser
        parser = PDFParser(file_path)
        
        # Extract all content
        result = parser.parse()
        
        # Process pages into sections
        processed_sections = []
        
        # Extract references
        reference_data = self._extract_reference_section([p for p in result["pages"].values()])
        self.reference_data = reference_data
        
        # Get page texts with context overlays 
        pages_data = []
        for page_num, page_text in result["pages"].items():
            prev_text = result["pages"].get(page_num - 1)
            next_text = result["pages"].get(page_num + 1)
            
            # Get any tables/images for this page
            tables = result["tables"].get(page_num, [])
            images = result["images"].get(page_num, [])
            
            # Create section
            section = Section(
                text=page_text,
                section_type='text',
                section_start_page_number=page_num,
                document_id=self.document_id,
                prev_page_text=prev_text,
                next_page_text=next_text,
                tables=tables, 
                images=images
            )
            # Process section data
            section_data = self._create_section_data(section)
            processed_sections.append(section_data)

        
        print(f"\n[DocumentProcessor] Processing completed:")
        print(f"Total pages: {len(processed_sections)}")
        print(f"Processing time: {time.time() - start_time:.2f}s")
        
        self.total_pages = len(processed_sections)
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[DocumentProcessor] Cleaned up temporary file: {file_path}")
        
        return processed_sections, reference_data



    def _create_section_data(self, section: Section) -> Dict[str, Any]:
        """Create section data dictionary with citations and references
        
        Input:
            section: Section - Section object with page content
            
        Output:
            Dict with section data:
            {
                'document_id': str,
                'section_id': str, 
                'section_type': str,
                'section_start_page_number': int,
                'content': {
                    'text': str,
                    'type': str,
                    'has_citations': bool
                },
                'citations': List[Dict],
                'elements': List[Dict]  # Tables and images
            }
        """

        print("[Create Section] get text context")
        # Get context-aware text
        section_text = section.get_context_text()

        print("section text: \n" , section_text)
        # Extract citations
        citations = self._extract_citations(section_text, self.reference_data)

        print("Citation extraction: ", citations)

        
        # Build elements list from tables and images
        elements = []
        
        # Add tables
        for table in section.tables:
            print("[Create Section] Found a table")
            print("table data:", table)
            elements.append({
                'type': 'table',
                'content': table
            })
            
            # Add images
        for image in section.images:
            print("[Create Section] Found an image")
            print("image data:", image)
            elements.append({
                'type': 'image',
                'page_number': image['page_number'],
                'image_index': image['image_index'],
                'width': image['width'],
                'height': image['height'],
                'filename': image['filename'],
                'path': image['path'],
                'extraction_date': image['extraction_date']
            })
        
        print("[Create Section] Create section data ")
        section_data = {
            'document_id': section.document_id,
            'section_id': section.section_id,
            'section_type': section.type,
            'section_start_page_number': section.section_start_page_number,
            'content': {
                'text': section_text,
                'type': section.type,
                'has_citations': bool(citations)
            },
            'citations': citations,
            'elements': elements
        }
        print("[Create Section] Section created ")
        
        return section_data
    


    def _preprocess_reference_text(self, page_texts: List[str]) -> List[str]:
        """Pre-process pages to join split references before main extraction"""
        processed_pages = []
        
        for page_text in page_texts:
            lines = page_text.split('\n')
            joined_lines = []
            current_line = ""
            
            for line in lines:
                # If line starts with any reference pattern, it's a new reference
                if (re.match(r'^\s*\[\d+\]', line) or      # [1]
                    re.match(r'^\s*\d+\.', line) or        # 1.
                    re.match(r'^\s*\[.*?\(\d{4}[a-z]?\)\]', line) or  # [Author(2023a)]
                    re.match(r'^\s*\([A-Za-z]+,\s*\d{4}\)', line)):   # (john,2024)
                    if current_line:  # Save previous reference if exists
                        joined_lines.append(current_line)
                    current_line = line
                # If we're in a reference and line doesn't start with pattern
                elif current_line:
                    current_line += " " + line.strip()
                else:
                    joined_lines.append(line)
                        
            # Add final reference
            if current_line:
                joined_lines.append(current_line)
                    
            processed_pages.append('\n'.join(joined_lines))
        
        return processed_pages

    def _extract_citations(self, text: str, reference_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract citations and match with references"""
        print(f"\n[Citation Extraction] Starting citation extraction")
        print(f"[Citation Extraction] Text length: {len(text)}")
        
        citations = []
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        
        # First handle numbered citations (keep existing functionality)
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
            
            # Match references (keep existing logic)
            if reference_data and 'entries' in reference_data:
                for ref_num in ref_numbers:
                    if ref_num in reference_data['entries']:
                        citation_data['references'].append(
                            reference_data['entries'][ref_num]
                        )
            
            citations.append(citation_data)

        # Add additional citation pattern matching
        for pattern_type, pattern in CITATION_PATTERNS.items():
            if pattern_type == 'numbered':
                continue  # Skip as already handled above
            
            for match in re.finditer(pattern, cleaned_text):
                citation_data = {
                    'text': match.group(0),
                    'type': pattern_type,
                    'position': match.span(),
                    'matched_text': match.group(1),
                    'references': []
                }
                citations.append(citation_data)
        
        print(f"[Citation Extraction] Found {len(citations)} citations")
        print(f"[Citation Extraction] Citations matched with references: {citations}")
        
        return citations

    def _extract_reference_section(self, page_texts: List[str]) -> Dict[str, Any]:
        """Extract reference section and entries from document"""
        print("\n[DocumentProcessor] Starting reference section extraction")

        page_texts = self._preprocess_reference_text(page_texts)
        print(" page text: \n", page_texts)
        
        reference_data = {
            'entries': {},
            'type': 'unknown',
            'start_page': None,
            'end_page': None
        }

        def is_likely_reference_entry(line: str) -> bool:
            """Check if line looks like a reference entry"""
            print("Line of text:", line)
            if not line.strip():
                return False
                
            patterns = [
                r'^\s*\[\d+\]',          # [1] Style
                r'^\s*\(\d+\)',          # (1) Style  
                r'^\s*\d+\.',            # 1. Style
                r'^[A-Z][a-zA-Z\'-]+',   # Starts with capitalized word
                r'^[A-Z]\.',             # Starts with initial
                r'et\s+al\.?,',          # et al.
                r'\(\d{4}\)[,.]',        # Year in parentheses
                r'doi:',                 # DOI
                r'ISBN:?',               # ISBN
                r'vol\.',                # Volume indicator
                r'pp\.',                 # Page indicators
                r'http[s]?://'           # URLs
            ]
            return any(re.search(pattern, line) for pattern in patterns)
        
        def combine_reference_lines(lines: List[str], start_idx: int) -> Tuple[str, int]:
            """Combines multi-line references into single string"""
            combined = lines[start_idx]
            current_idx = start_idx + 1
            
            while current_idx < len(lines):
                next_line = lines[current_idx].strip()
                
                # Stop if we hit next reference (any pattern)
                if any(re.match(pattern, next_line) for pattern in REFERENCE_PATTERNS.values()):
                    break
                    
                # Stop if we found completion marker
                if re.search(r'\d{4}\.|\b(?:https?://|www\.)\S+', next_line):
                    combined += ' ' + next_line
                    break
                    
                combined += ' ' + next_line
                current_idx += 1
                
            return combined, current_idx - 1

        # Process each page (keeping your existing page processing)
        reference_section_found = False
        for page_idx, page_text in enumerate(page_texts):
            if not page_text:
                continue
                
            lines = page_text.split('\n')
            
            # Look for reference section marker
            for line_idx, line in enumerate(lines):
                for pattern in REFERENCE_SECTION_TITLES:
                    if re.search(pattern, line.lower().strip()):
                        print(f"[DocumentProcessor] Found potential reference marker on page {page_idx + 1}")
                        reference_section_found = True
                        if reference_data['start_page'] is None:
                            reference_data['start_page'] = page_idx + 1
                        break
                if reference_section_found:
                    break

            if reference_section_found:
                # Process references line by line
                current_line = line_idx + 1
                while current_line < len(lines):
                    line = lines[current_line].strip()
                    
                    # First try all reference patterns
                    for ref_type, pattern in REFERENCE_PATTERNS.items():
                        ref_match = re.match(pattern, line)
                        if ref_match:
                            # Get reference identifier based on type
                            if ref_type == 'numbered_bracket':
                                ref_id = ref_match.group(1)
                            elif ref_type == 'numbered_dot':
                                ref_id = ref_match.group(1)
                            else:
                                ref_id = ref_match.group(1)
                                
                            # Combine multi-line reference
                            full_ref, current_line = combine_reference_lines(lines, current_line)
                            
                            if len(full_ref) > 10:  # Basic validation
                                reference_data['entries'][ref_id] = {
                                    'text': full_ref,
                                    'type': ref_type
                                }
                            break
                    
                    current_line += 1

        # Continue processing subsequent pages (keeping your existing logic)
        if reference_section_found:
            for page_idx in range(reference_data['start_page'], len(page_texts)):
                page_text = page_texts[page_idx]
                lines = page_text.split('\n')
                current_line = 0
                while current_line < len(lines):
                    line = lines[current_line].strip()
                    
                    # Process reference patterns
                    for ref_type, pattern in REFERENCE_PATTERNS.items():
                        ref_match = re.match(pattern, line)
                        if ref_match:
                            ref_id = ref_match.group(1)
                            full_ref, current_line = combine_reference_lines(lines, current_line)
                            
                            if len(full_ref) > 10:
                                reference_data['entries'][ref_id] = {
                                    'text': full_ref,
                                    'type': ref_type
                                }
                            break
                    
                    current_line += 1
                reference_data['end_page'] = page_idx + 1

        if reference_data['entries']:
            print(f"[DocumentProcessor] Found {len(reference_data['entries'])} references!")
            print("reference_data \n:", reference_data['entries'])
        
        return reference_data
    

    