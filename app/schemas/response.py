from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from app.schemas.request import ChaosConfig

class ScoreExplanation(BaseModel):
    search: float = Field(..., description="Search index base score")
    recommendation: float = Field(..., description="ML recommendation score")
    external: float = Field(..., description="External signal score")

class SearchResult(BaseModel):
    doc_id: str = Field(..., description="Document identifier")
    title: str = Field(..., description="Document title")
    text: str = Field(..., description="Document text snippet")
    score: float = Field(..., ge=0.0, le=1.0, description="Final combined score")
    explanations: ScoreExplanation = Field(..., description="Score breakdown by component")

class ResponseMeta(BaseModel):
    latency_ms: int = Field(..., description="Total request latency in milliseconds")
    model_version: str = Field(default="mock_v1", description="ML model version identifier")
    components_called: List[str] = Field(..., description="List of components invoked")
    cache_hit: bool = Field(default=False, description="Whether cache was used")

class SearchResponse(BaseModel):
    query: str = Field(..., description="Original search query")
    parsed_query: Dict[str, Any] = Field(..., description="Parsed query details")
    results: List[SearchResult] = Field(..., description="Ranked search results")
    meta: ResponseMeta = Field(..., description="Response metadata")

class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Service health status")
    components: Dict[str, str] = Field(..., description="Component health checks")
    version: str = Field(default="1.0.0", description="Service version")

class ChaosConfigResponse(BaseModel):
    config: ChaosConfig = Field(..., description="Current chaos configuration")
    message: str = Field(..., description="Status message")

class ErrorDetail(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")

class ErrorResponse(BaseModel):
    detail: ErrorDetail
