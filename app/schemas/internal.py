from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class QueryIntent(str, Enum):
    SEARCH = "search"
    DISCOVERY = "discovery"

class ParsedQuery(BaseModel):
    original: str
    normalized: str
    tokens: List[str]
    intent: QueryIntent
    token_count: int

class Document(BaseModel):
    doc_id: str
    title: str
    text: str
    category: str
    embedding: List[float]  # Mock 8-dim embedding

class SearchIndexResult(BaseModel):
    doc_id: str
    title: str
    text: str
    base_score: float
    match_count: int  # Number of query tokens matched

class FeatureVector(BaseModel):
    query_length: int
    query_token_count: int
    user_id_hash: int  # Stable hash of user_id
    doc_length: int
    doc_category_encoded: int
    query_doc_overlap: float  # Jaccard similarity
    embedding_dot_product: float  # Dot product of query and doc embeddings

class ModelPrediction(BaseModel):
    score: float
    confidence: float
    model_version: str = "mock_v1"

class ExternalSignal(BaseModel):
    source: str
    relevance_score: float
    description_length: int
    popularity_proxy: Optional[float] = None
