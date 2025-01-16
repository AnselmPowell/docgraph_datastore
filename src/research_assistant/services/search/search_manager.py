# src/research_assistant/services/search/search_manager.py

from typing import Dict, List, Any
from ...models import DocumentMetadata
from ..document_searcher import DocumentSearcher
from ..cache_manager import DocumentCacheManager

class SearchManager:
    """Manages document search operations"""

    def __init__(self):
        print("[SearchManager] Initializing")
        self.searcher = DocumentSearcher()
        self.cache_manager = DocumentCacheManager()

    def prepare_sections_for_search(self, sections: List[Dict]) -> List[Dict]:
        """Prepare document sections for search"""
        print("[SearchManager] Preparing sections for search")
        search_sections = []
        
        for section in sections:
            search_section = {
                'text': section['content']['text'],
                'section_id': section['section_id'],
                'page_number': section['section_start_page_number'],
                'section_type': section['content']['type'],
                'start_text': section['pointer']['section_start_text'],
                'url_fragment': f"page={section['section_start_page_number']}",
                'elements': section.get('elements', []),
                'citations': section.get('citations', []),
                'matching_context': "",
                'matching_theme': "",
                'matching_keywords': [],
                'matching_similar_keywords': [],
                'relevance_type': [],
                'title_group_number': section['pointer'].get('title_group_number'),
                'title_group_text': section['pointer'].get('title_text')
            }
            search_sections.append(search_section)
            
        print(f"[SearchManager] Prepared {len(search_sections)} sections")
        return search_sections

    def search_documents(
        self,
        document_ids: List[str],
        context: str,
        theme: str,
        keywords: List[str]
    ) -> Dict:
        """Search across multiple documents"""
        print(f"[SearchManager] Searching {len(document_ids)} documents")
        print(f"[SearchManager] Context: {context}")
        print(f"[SearchManager] Theme: {theme}")
        print(f"[SearchManager] Keywords: {keywords}")

        try:
            # Get documents
            documents = DocumentMetadata.objects.filter(
                id__in=document_ids,
                processing_status='completed'
            )

            if not documents:
                raise ValueError("No valid documents found")

            results = []
            for document in documents:
                print(f"[SearchManager] Processing document: {document.id}")
                
                # Get cached sections
                doc_data = self.cache_manager.get_document_data_sync(str(document.id))
                if not doc_data:
                    print(f"[SearchManager] No cached data for document {document.id}")
                    continue

                # Prepare sections for search
                search_sections = self.prepare_sections_for_search(doc_data['sections'])
                
                # Search document
                search_result = self.searcher.search_document(
                    search_sections,
                    context,
                    theme,
                    keywords,
                    document.summary,
                    str(document.id),
                    document.reference
                )

                # Format result
                doc_result = {
                    'document_id': str(document.id),
                    'title': document.title,
                    'authors': document.authors,
                    'summary': document.summary,
                    'file_name': document.file_name,
                    'relevance_score': search_result['relevance_score'],
                    'total_matches': len(search_result['relevant_sections']),
                    'matching_sections': [
                        {
                            'section_id': section['section_id'],
                            'page_number': section['page_number'],
                            'start_text': section['start_text'],
                            'url_fragment': section['url_fragment'],
                            'content': section['text'],
                            'matching_context': section.get('matching_context', ''),
                            'matching_theme': section.get('matching_theme', ''),
                            'matching_keywords': section.get('matching_keywords', []),
                            'citations': section.get('citations', []),
                            'relevance_type': section.get('relevance_type', [])
                        }
                        for section in search_result['relevant_sections']
                    ]
                }
                results.append(doc_result)

            # Sort by relevance score
            results.sort(key=lambda x: x['relevance_score'], reverse=True)

            return {
                'status': 'success',
                'total_documents': len(results),
                'results': results
            }

        except Exception as e:
            print(f"[SearchManager] Error during search: {str(e)}")
            raise


