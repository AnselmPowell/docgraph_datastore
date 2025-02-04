# src/research_assistant/services/search/search_manager.py

from typing import Dict, List, Any
from ...models import DocumentMetadata, DocumentSection
from ..document_searcher import DocumentSearcher


class SearchManager:
    def __init__(self):
        print("[SearchManager] Initializing")
        self.searcher = DocumentSearcher()

    def prepare_sections_for_search(self, sections: List[Dict]) -> List[Dict]:
        search_sections = []
        for section in sections:
            # Added validation and type conversion
            section_id = str(section.id) if hasattr(section, 'id') else None
            content = section.content if hasattr(section, 'content') else section.get('text', '')
            
            search_section = {
                'text': content,
                'section_id': section_id,
                'page_number': int(section.section_start_page_number),
                'section_type': section.section_type,
                'start_text': content[:100] if content else "",
                'elements': section.get_elements() if hasattr(section, 'get_elements') else [],
                'citations': section.citations if hasattr(section, 'citations') else {},
                'matching_context': "",
                'matching_keywords': [],
                'matching_similar_keywords': [],
                'relevance_type': []
            }
            search_sections.append(search_section)
        return search_sections

    def search_documents(
        self,
        documents,
        context: str,
        keywords: List[str]
    ) -> Dict:
        print(f"[SearchManager] Searching document {documents} documents")
        print(f"[SearchManager] Context: {context}")
        print(f"[SearchManager] Keywords: {keywords}")

        all_documents = DocumentMetadata.objects.all()
    
        # Print the count of documents
        print(f"Total Documents: {all_documents.count()}")
        
        # Iterate and print each document's details
        for doc in all_documents:
            print(f"ID: {doc.id}")
            print(f"Title: {doc.title}")
            print(f"Authors: {doc.authors}")
            print(f"Publication Date: {doc.publication_date}")
            print(f"Publisher: {doc.publisher}")
            print(f"DOI: {doc.doi}")
            print(f"URL: {doc.url}")
            print(f"File Name: {doc.file_name}")

        # Extract file names from the input
        file_names = documents.get('file_name', [])
        if not file_names:
            raise ValueError("No file names provided for search.")

        # Ensure file_names is a list
        if not isinstance(file_names, list):
            file_names = [file_names]

        print(f"Filtering for file_names: {file_names}")
        documents = DocumentMetadata.objects.filter(file_name__in=file_names)

        if not documents.exists():
            print(f"No documents found for file_names: {file_names}")
            raise ValueError(f"No valid documents found for file_names: {file_names}")

        results = []
        print(" documents found")
        for document in documents:
            print(f"[SearchManager] Processing document: {document.file_name}")
            
            # Get all sections for document directly from model
            sections = DocumentSection.objects.filter(
                document=document,
                content__isnull=False  # Ensure no empty sections
            ).order_by('section_start_page_number').select_related('document')
            
            search_sections = self.prepare_sections_for_search(sections)
            
            print("start section search")
            search_result = self.searcher.search_document(
                search_sections,
                context,
                keywords,
                document.summary,
                document.reference
            )

            doc_result = {
                'document_id': str(document.id),
                'question': context,
                'keywords': keywords,
                'title': document.title,
                'authors': document.authors,
                'summary': document.summary,
                'file_name': document.file_name,
                'relevance_score': search_result['relevance_score'],
                'total_matches': search_result['total_matches'],
                'matching_sections': [
                    {
                        'section_id': section['section_id'],
                        'page_number': section['page_number'],
                        'start_text': section['start_text'],
                        # Context matches with citations
                        'context_matches': [
                            {
                                'text': match['text'],
                                'citations': match['citations']
                            }
                            for match in section['context_matches']
                        ],
                        # Keyword matches
                        'keyword_matches': [
                            {
                                'keyword': match['keyword'],
                                'text': match['text']
                            }
                            for match in section['keyword_matches']
                        ],
                        # Similar keyword matches
                        'similar_matches': [
                            {
                                'similar_keyword': match['similar_keyword'],
                                'text': match['text']
                            }
                            for match in section['similar_matches']
                        ]
                    }
                    for section in search_result['relevant_sections']
                ]
            }
            results.append(doc_result)

            # Sort by relevance score
            results.sort(key=lambda x: x['relevance_score'], reverse=True)

            return {
                'status': 'success',
                'total_matches': len(results),
                'results': results
            }