import logging
from typing import List, Dict, Optional
from opentelemetry import trace
from app.schemas.internal import SearchIndexResult, ModelPrediction, ExternalSignal
from app.schemas.response import SearchResult, ScoreExplanation
from app.core.config import settings

logger = logging.getLogger(__name__)

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
        span = trace.get_current_span()

        # Add ranking configuration to span
        span.set_attribute("ranking.weight_search", self.weight_search)
        span.set_attribute("ranking.weight_recommendation", self.weight_recommendation)
        span.set_attribute("ranking.weight_external", self.weight_external)
        span.set_attribute("ranking.num_input_documents", len(search_results))
        span.set_attribute("ranking.num_predictions_available", len(model_predictions))
        span.set_attribute("ranking.has_external_signal", external_signal is not None)

        # External signal score (same for all docs)
        external_score = (
            external_signal.relevance_score
            if external_signal else 0.0
        )

        if external_signal:
            span.set_attribute("ranking.external_score", round(external_score, 3))
            span.set_attribute("ranking.external_source", external_signal.source)

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

        # Add result attributes to span
        span.set_attribute("ranking.num_output_results", len(ranked_results))

        if ranked_results:
            final_scores = [r.score for r in ranked_results]
            span.set_attribute("ranking.final_score_min", round(min(final_scores), 3))
            span.set_attribute("ranking.final_score_max", round(max(final_scores), 3))
            span.set_attribute("ranking.final_score_avg", round(sum(final_scores) / len(final_scores), 3))
            span.set_attribute("ranking.top_doc_id", ranked_results[0].doc_id)
            span.set_attribute("ranking.top_doc_title", ranked_results[0].title)
            span.set_attribute("ranking.top_final_score", round(ranked_results[0].score, 3))
            span.set_attribute("ranking.top_3_doc_ids", ",".join([r.doc_id for r in ranked_results[:3]]))

            # Add score component analysis for top result
            top_result = ranked_results[0]
            span.set_attribute("ranking.top_search_score", round(top_result.explanations.search, 3))
            span.set_attribute("ranking.top_recommendation_score", round(top_result.explanations.recommendation, 3))
            span.set_attribute("ranking.top_external_score", round(top_result.explanations.external, 3))

            # Calculate prediction coverage
            docs_with_predictions = sum(1 for r in ranked_results if r.explanations.recommendation > 0)
            prediction_coverage = docs_with_predictions / len(ranked_results)
            span.set_attribute("ranking.prediction_coverage", round(prediction_coverage, 3))
            span.set_attribute("ranking.docs_with_predictions", docs_with_predictions)

        return ranked_results
