from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import time
import logging

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from app.core.metrics import (
    record_search_query, record_model_prediction,
    record_external_api_call, record_component_duration
)

from app.schemas.request import SearchRequest, ChaosConfig
from app.schemas.response import SearchResponse, ResponseMeta, HealthResponse, ChaosConfigResponse
from app.schemas.internal import ParsedQuery

from app.core.query_parser import QueryParser
from app.core.ranker import Ranker
from app.core.chaos import chaos_manager
from app.core.config import settings

from app.search.index import SearchIndex
from app.recommendation.features import FeatureBuilder
from app.recommendation.model import MockMLModel
from app.recommendation.errors import ModelError
from app.external.wikipedia import WikipediaClient

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

router = APIRouter()

# Initialize components
query_parser = QueryParser()
search_index = SearchIndex(settings.database_path)
feature_builder = FeatureBuilder(settings.database_path)
ml_model = MockMLModel()
wikipedia_client = WikipediaClient()
ranker = Ranker()

@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    user_id: str = Query(..., min_length=1, max_length=100, description="User identifier"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum results")
):
    """
    Main search endpoint

    Orchestrates all components:
    1. Parse query
    2. Search index
    3. Build features and get ML predictions
    4. Fetch external signals
    5. Rank and return results
    """
    start_time = time.time()
    components_called = []

    # Add user_id to the root span for filtering in SigNoz
    current_span = trace.get_current_span()
    current_span.set_attribute("user_id", user_id)
    current_span.set_attribute("query", q)
    current_span.set_attribute("limit", limit)

    # 1. Parse query
    with tracer.start_as_current_span("query_parser.parse") as span:
        span.set_attribute("query.length", len(q))
        component_start = time.time()

        parsed_query = query_parser.parse(q)

        span.set_attribute("query.token_count", parsed_query.token_count)
        span.set_attribute("query.intent", parsed_query.intent.value)
        components_called.append("query_parser")

        component_duration = (time.time() - component_start) * 1000
        record_component_duration("query_parser", component_duration)
        record_search_query(parsed_query.intent.value)

    # 2. Search index
    with tracer.start_as_current_span("search_index.search") as span:
        span.set_attribute("search.limit", limit)
        component_start = time.time()

        search_results = search_index.search(parsed_query, limit=limit)

        span.set_attribute("search.result_count", len(search_results))
        components_called.append("search_index")

        component_duration = (time.time() - component_start) * 1000
        record_component_duration("search_index", component_duration)

    # 3. ML predictions (per-document spans)
    model_predictions = {}
    successful_predictions = 0
    failed_predictions = 0

    with tracer.start_as_current_span("recommendation_engine") as batch_span:
        for doc in search_results:
            prediction_start = time.time()

            with tracer.start_as_current_span("model.predict") as pred_span:
                pred_span.set_attribute("doc_id", doc.doc_id)
                pred_span.set_attribute("model.version", ml_model.version)

                try:
                    features = feature_builder.build_features(parsed_query, doc, user_id)
                    prediction = ml_model.predict(features)

                    pred_span.set_attribute("model.score", prediction.score)
                    pred_span.set_attribute("model.confidence", prediction.confidence)

                    model_predictions[doc.doc_id] = prediction
                    successful_predictions += 1

                    prediction_duration = (time.time() - prediction_start) * 1000
                    record_model_prediction("success", prediction_duration, prediction.score)

                    if "recommendation_engine" not in components_called:
                        components_called.append("recommendation_engine")

                except ModelError as e:
                    pred_span.record_exception(e)
                    pred_span.set_status(Status(StatusCode.ERROR, str(e)))
                    failed_predictions += 1

                    prediction_duration = (time.time() - prediction_start) * 1000
                    record_model_prediction("failure", prediction_duration)

                    logger.warning("Model prediction failed", extra={
                        "doc_id": doc.doc_id,
                        "error": str(e)
                    })

        batch_span.set_attribute("model.predictions.successful", successful_predictions)
        batch_span.set_attribute("model.predictions.failed", failed_predictions)

    # 4. Wikipedia API
    external_signal = None
    with tracer.start_as_current_span("wikipedia_client.get_signal") as span:
        try:
            external_signal = await wikipedia_client.get_signal(parsed_query)
            if external_signal:
                span.set_attribute("external.source", "wikipedia")
                span.set_attribute("external.relevance_score", external_signal.relevance_score)
                components_called.append("wikipedia_api")
                record_external_api_call("wikipedia", "success")
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            record_external_api_call("wikipedia", "failure")
            logger.warning("Wikipedia API failed", extra={"error": str(e)})

    # 5. Ranker
    with tracer.start_as_current_span("ranker.rank") as span:
        component_start = time.time()

        ranked_results = ranker.rank(search_results, model_predictions, external_signal)

        span.set_attribute("ranking.result_count", len(ranked_results))
        components_called.append("ranker")

        component_duration = (time.time() - component_start) * 1000
        record_component_duration("ranker", component_duration)

    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)

    # Build response
    return SearchResponse(
        query=q,
        parsed_query={
            "normalized": parsed_query.normalized,
            "tokens": parsed_query.tokens,
            "intent": parsed_query.intent.value,
            "token_count": parsed_query.token_count
        },
        results=ranked_results,
        meta=ResponseMeta(
            latency_ms=latency_ms,
            model_version="mock_v1",
            components_called=components_called
        )
    )

@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    components = {
        "api": "healthy",
        "database": "healthy",
        "ml_model": "healthy",
        "external_api": "healthy"
    }

    # Could add actual health checks here

    return HealthResponse(
        status="healthy",
        components=components,
        version=settings.app_version
    )

@router.post("/chaos/config", response_model=ChaosConfigResponse)
async def update_chaos_config(config: ChaosConfig):
    """Update chaos engineering configuration"""
    chaos_manager.update_config(config)
    return ChaosConfigResponse(
        config=config,
        message="Chaos configuration updated successfully"
    )

@router.get("/chaos/config", response_model=ChaosConfigResponse)
async def get_chaos_config():
    """Get current chaos engineering configuration"""
    config = chaos_manager.get_config()
    return ChaosConfigResponse(
        config=config,
        message="Current chaos configuration"
    )
