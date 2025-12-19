from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import time

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

    # 1. Parse query
    parsed_query = query_parser.parse(q)
    components_called.append("query_parser")

    # 2. Search index
    search_results = search_index.search(parsed_query, limit=limit)
    components_called.append("search_index")

    # 3. Get ML predictions for each result
    model_predictions = {}
    for doc in search_results:
        try:
            features = feature_builder.build_features(parsed_query, doc, user_id)
            prediction = ml_model.predict(features)
            model_predictions[doc.doc_id] = prediction
            if "recommendation_engine" not in components_called:
                components_called.append("recommendation_engine")
        except ModelError:
            # Continue without prediction for this document
            pass

    # 4. Fetch external signal
    external_signal = None
    try:
        external_signal = await wikipedia_client.get_signal(parsed_query)
        if external_signal:
            components_called.append("wikipedia_api")
    except Exception:
        # Continue without external signal
        pass

    # 5. Rank results
    ranked_results = ranker.rank(search_results, model_predictions, external_signal)
    components_called.append("ranker")

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
