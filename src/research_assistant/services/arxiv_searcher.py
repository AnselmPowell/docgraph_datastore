# src/research_assistant/services/arxiv_searcher.py
import urllib.parse
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

class ArxivSearcher:
    """Service for searching arXiv papers"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    NAMESPACE = {'atom': 'http://www.w3.org/2005/Atom',
                 'arxiv': 'http://arxiv.org/schemas/atom'}
    
    def __init__(self):
        print("[ArxivSearcher] Initializing")
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search arXiv for papers matching query"""
        print(f"[ArxivSearcher] Searching for: {query}")
        
        # URL encode the query
        encoded_query = urllib.parse.quote(query)
        
        # Build the request URL
        request_url = f"{self.BASE_URL}?search_query=all:{encoded_query}&start=0&max_results={max_results}"
        
        try:
            # Make the request
            response = requests.get(request_url)
            response.raise_for_status()
            
            # Parse the XML response
            return self._parse_response(response.text)
            
        except requests.RequestException as e:
            print(f"[ArxivSearcher] Error during arXiv API request: {str(e)}")
            raise
    
    def _parse_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse arXiv API response XML"""
        root = ET.fromstring(xml_content)
        results = []
        
        # Parse each entry
        for entry in root.findall('.//atom:entry', self.NAMESPACE):
            paper = {}
            
            # Extract basic metadata
            paper['id'] = self._get_text(entry, './/atom:id')
            paper['title'] = self._get_text(entry, './/atom:title')
            paper['summary'] = self._get_text(entry, './/atom:summary')
            paper['published'] = self._get_text(entry, './/atom:published')
            paper['updated'] = self._get_text(entry, './/atom:updated')
            
            # Extract authors
            authors = []
            for author in entry.findall('.//atom:author', self.NAMESPACE):
                name = self._get_text(author, './/atom:name')
                if name:
                    authors.append(name)
            paper['authors'] = authors
            
            # Extract links
            links = []
            for link in entry.findall('.//atom:link', self.NAMESPACE):
                href = link.get('href')
                rel = link.get('rel')
                title = link.get('title')
                if href:
                    links.append({
                        'href': href,
                        'rel': rel,
                        'title': title
                    })
            paper['links'] = links
            
            # Extract primary category
            primary_category = entry.find('.//arxiv:primary_category', self.NAMESPACE)
            if primary_category is not None:
                paper['primary_category'] = primary_category.get('term')
            
            # Extract all categories
            categories = []
            for category in entry.findall('.//atom:category', self.NAMESPACE):
                term = category.get('term')
                if term:
                    categories.append(term)
            paper['categories'] = categories
            
            # Add to results
            results.append(paper)
        
        return results
    
    def _get_text(self, element: ET.Element, xpath: str) -> Optional[str]:
        """Safely extract text from an XML element"""
        found = element.find(xpath, self.NAMESPACE)
        if found is not None and found.text:
            return found.text.strip()
        return None