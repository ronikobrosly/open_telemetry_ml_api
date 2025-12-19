from typing import List, Dict, Optional
from app.schemas.internal import SearchIndexResult, ModelPrediction, ExternalSignal
from app.schemas.response import SearchResult, ScoreExplanation
from app.core.config import settings

class Ranker:
    """
    Combine signals from multiple components and rank results

    Ranking Algorithm:
    final_score = w1*search_score + w2*recommendation_score + w3*external_score

    Where weights are configurable (default: 0.5, 0.3, 0.2)
    """

    def __init__(self):
        self.weight_search = settings.weight_search
        self.weight_recommendation = settings.weight_recommendation
        self.weight_external = settings.weight_external

    def rank(
        self,
        search_results: List[SearchIndexResult],
        model_predictions: Dict[str, ModelPrediction],
        external_signal: Optional[ExternalSignal]
    ) -> List[SearchResult]:
        """
        Rank and combine results

        Args:
            search_results: Results from search index
            model_predictions: Dict mapping doc_id to ModelPrediction
            external_signal: Signal from external API (applied globally)

        Returns:
            Ranked list of SearchResult objects
        """
        # External signal score (same for all docs)
        external_score = (
            external_signal.relevance_score
            if external_signal else 0.0
        )

        ranked_results = []

        for doc in search_results:
            # Get prediction for this document
            prediction = model_predictions.get(doc.doc_id)
            recommendation_score = prediction.score if prediction else 0.0

            # Calculate final score
            final_score = (
                self.weight_search * doc.base_score +
                self.weight_recommendation * recommendation_score +
                self.weight_external * external_score
            )

            # Create explanation
            explanation = ScoreExplanation(
                search=doc.base_score,
                recommendation=recommendation_score,
                external=external_score
            )

            ranked_results.append(SearchResult(
                doc_id=doc.doc_id,
                title=doc.title,
                text=doc.text,
                score=final_score,
                explanations=explanation
            ))

        # Sort by final score descending
        ranked_results.sort(key=lambda x: x.score, reverse=True)

        return ranked_results
