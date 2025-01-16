# src/research_assistant/services/search/relevance_scorer.py

from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class RelevanceWeights:
    """Weights for different relevance factors"""
    context_weight: float = 1.0  # Context matches most important
    theme_weight: float = 0.8    # Theme alignment second
    keyword_weight: float = 0.6  # Direct keyword matches
    similar_weight: float = 0.4  # Similar concept matches
    citation_bonus: float = 0.2  # Bonus for cited matches

class RelevanceScorer:
    """Enhanced relevance scoring for document sections"""

    def __init__(self, weights: Optional[RelevanceWeights] = None):
        print("[RelevanceScorer] Initializing")
        self.weights = weights or RelevanceWeights()

    def calculate_section_score(
        self,
        section_data: Dict,
        total_sections: int
    ) -> Dict[str, float]:
        """Calculate detailed relevance scores for a section"""
        print(f"[RelevanceScorer] Calculating section score")

        # Base component scores
        scores = {
            'context_score': 0.0,
            'theme_score': 0.0,
            'keyword_score': 0.0,
            'similar_score': 0.0,
            'citation_score': 0.0
        }

        # Context scoring
        if section_data.get('matching_context'):
            scores['context_score'] = self.weights.context_weight
            if section_data.get('context_citations'):
                scores['citation_score'] += self.weights.citation_bonus

        # Theme scoring
        if section_data.get('matching_theme'):
            scores['theme_score'] = self.weights.theme_weight
            if section_data.get('theme_citations'):
                scores['citation_score'] += self.weights.citation_bonus

        # Keyword scoring
        keyword_matches = len(section_data.get('matching_keywords', []))
        if keyword_matches:
            scores['keyword_score'] = self.weights.keyword_weight * min(keyword_matches / 3, 1.0)

        # Similar concept scoring
        similar_matches = len(section_data.get('matching_similar_keywords', []))
        if similar_matches:
            scores['similar_score'] = self.weights.similar_weight * min(similar_matches / 3, 1.0)

        # Calculate combined score
        total_score = sum(scores.values())
        normalized_score = min(total_score * 10, 100)  # Scale to 0-100

        return {
            'component_scores': scores,
            'total_score': normalized_score
        }

    def calculate_document_score(
        self,
        sections: List[Dict],
        total_sections: int,
        has_summary_match: bool
    ) -> Dict[str, float]:
        """Calculate overall document relevance score"""
        print(f"[RelevanceScorer] Calculating document score for {len(sections)} sections")

        # Calculate scores for all sections
        section_scores = [
            self.calculate_section_score(section, total_sections)
            for section in sections
        ]

        # Get max scores for each component
        max_scores = {
            component: max(
                score['component_scores'][component] 
                for score in section_scores
            )
            for component in section_scores[0]['component_scores'].keys()
        }

        # Calculate document level metrics
        metrics = {
            'max_section_score': max(s['total_score'] for s in section_scores),
            'avg_section_score': np.mean([s['total_score'] for s in section_scores]),
            'relevant_section_ratio': len(sections) / total_sections,
            'component_coverage': max_scores,
            'has_summary_match': float(has_summary_match) * 0.1  # 10% bonus for summary match
        }

        # Calculate final document score
        base_score = (
            metrics['max_section_score'] * 0.4 +  # Best section
            metrics['avg_section_score'] * 0.3 +  # Average quality
            metrics['relevant_section_ratio'] * 20 +  # Coverage
            sum(max_scores.values()) * 5  # Component diversity
        )

        # Apply summary match bonus
        final_score = min(base_score * (1 + metrics['has_summary_match']), 100)

        return {
            'final_score': final_score,
            'metrics': metrics
        }

    def sort_results(self, results: List[Dict]) -> List[Dict]:
        """Sort search results by relevance score"""
        return sorted(
            results,
            key=lambda x: x['relevance_score'],
            reverse=True
        )