# Search + Recommendation FastAPI Service

## Overview

This document provides a **complete technical specification** for a demo-friendly FastAPI microservice architecture that will serve as a showcase of the value of OpenTelemetry (Otel).

This API contains a ML model. The ML model in this project serves as a recommendation engine that provides personalized relevance scoring beyond simple keyword matching. After the search index returns documents based on text similarity, the ML model analyzes features like query-document overlap, embedding similarity, user characteristics, and document attributes to predict how relevant each document is for that specific user and query context. This recommendation score (weighted at 30% by default) is then combined with the base search score (50%) and external Wikipedia signals (20%) to produce the final ranking. Critically, because this is a demo service for OpenTelemetry, the ML model is intentionally designed to exhibit realistic failure modes—it can timeout, throw inference errors, or return invalid predictions—making it an excellent component for demonstrating how to observe, trace, and debug ML systems in production where model behavior is often the most complex and opaque part of the system.

The service is intentionally designed to:

* Feel realistic to data scientists and ML engineers
* Use mocked modeling components (to simulate ML behavior and failures)
* Include at least one **real external API call** to demo Otel
* Naturally decompose into spans, metrics, and errors for Otel demos

**Implementation Philosophy:** This spec provides deterministic implementation details to minimize arbitrary choices. Where randomness is needed (e.g., chaos injection), specific algorithms and seed strategies are provided.

---

## 1. High-Level Architecture

```
Client
  |
  v
Search API (FastAPI)
  |
  +--> Query Parser
  |
  +--> Search Index (local / SQLite / in-memory)
  |
  +--> Recommendation Engine (mock ML)
  |        |
  |        +--> Feature Builder
  |        +--> Model Scorer (mocked)
  |
  +--> External Signals API (REAL HTTP call)
  |        (e.g. Wikipedia / Open-Meteo / News API)
  |
  +--> Ranker
  |
  +--> Cache (optional, later)
  |
  v
Response
```

This is a **single microservice** with clearly separated *logical subsystems* that later map cleanly to OpenTelemetry spans.

---

## 2. Core API Surface

### Primary Endpoint

```http
GET /search?q=machine+learning&user_id=123
```

### Optional Supporting Endpoints (Useful for Demos)

```http
GET /health
GET /metrics        # later
POST /chaos/toggle  # simulate failures
```

---

## 3. Request Flow (Step-by-Step)

### 3.1 Request Ingress

* Accepts `q`, `user_id`, optional `limit`
* Validates inputs
* Attaches request context

**Why it matters later (Otel):**

* Root span
* Request attributes: query length, user_id, limit

---

### 3.2 Query Parsing & Normalization

**Example logic:**

* Lowercase
* Tokenize
* Remove stopwords
* Detect intent (search vs discovery)

**Example output:**

```json
{
  "tokens": ["machine", "learning"],
  "intent": "search"
}
```

**Failure modes:**

* Empty query
* Excessively long query

---

### 3.3 Search Index Lookup (Local / Fake DB)

**Implementation options:**

* In-memory list of documents
* SQLite
* DuckDB
* JSON file loaded at startup

**What it simulates:**

* Keyword-based retrieval
* Latency variability
* Occasional slow query

**Example output:**

```json
[
  {"doc_id": "A1", "text": "...", "base_score": 0.82},
  {"doc_id": "B7", "text": "...", "base_score": 0.76}
]
```

---

### 3.4 Recommendation Engine (Mock ML)

This component intentionally mirrors a real ML inference pipeline.

#### Subcomponents

**Feature Builder**

* Query features (length, token count)
* User features (fake profile)
* Item features (fake embeddings)

**Mock Model**

* Returns a score and confidence
* Occasionally:

  * Throws an exception
  * Times out
  * Returns invalid values

**Example mock model:**

```python
import random

def score(features):
    if random.random() < 0.05:
        raise ModelError("Inference failed")
    return random.random()
```

**Why this matters:**

* Model failures are excellent observability demos
* ML-specific spans and attributes make traces intuitive

---

### 3.5 External Signals API (REAL HTTP Call)

At least one **real external dependency** is included to create authentic latency and failure behavior.

#### Recommended APIs

**Wikipedia REST API (Strongly Recommended)**

* No authentication required
* High uptime
* Query-based

Example:

```http
https://en.wikipedia.org/api/rest_v1/page/summary/{topic}
```

Use cases:

* Topic popularity proxy
* Description length as relevance signal
* External context boost

Other viable options:

* Open-Meteo API
* Hacker News Algolia API

**Why this matters:**

* Real DNS + HTTP latency
* Natural distributed tracing later

---

### 3.6 Ranking & Fusion Layer

Combine signals from multiple subsystems:

```python
final_score = (
    0.5 * search_score +
    0.3 * recommendation_score +
    0.2 * external_signal_score
)
```

Capabilities:

* Feature flags
* Ranking regressions
* Controlled behavior changes

---

### 3.7 Response Assembly

Example response:

```json
{
  "query": "machine learning",
  "results": [
    {
      "doc_id": "A1",
      "score": 0.91,
      "explanations": {
        "search": 0.82,
        "recommendation": 0.88,
        "external": 0.67
      }
    }
  ],
  "meta": {
    "latency_ms": 312,
    "model_version": "mock_v1"
  }
}
```

This structure makes system behavior easy to reason about.

---

## 4. Failure & Chaos Injection

Introduce a lightweight chaos configuration:

```python
CHAOS = {
  "model_failure_rate": 0.05,
  "external_api_timeout_rate": 0.1,
  "slow_search_rate": 0.2
}
```

Later, toggling these values instantly produces observable changes in traces and metrics.

---

## 5. Suggested Folder Structure

```text
app/
├── main.py
├── api/
│   └── search.py
├── core/
│   ├── query_parser.py
│   ├── ranker.py
│   └── chaos.py
├── search/
│   └── index.py
├── recommendation/
│   ├── features.py
│   ├── model.py
│   └── errors.py
├── external/
│   └── wikipedia.py
├── schemas/
│   └── response.py
└── utils/
    └── timing.py
```

This mirrors real-world ML service layouts and keeps concerns cleanly separated.

---

## 6. Why This Architecture Is Otel Gold (Later)

Even before adding observability tooling, this design already provides:

* Clear span boundaries
* Natural parent/child relationships
* ML-specific failure modes
* Real external dependencies
* Deterministic vs stochastic behavior

When OpenTelemetry is added:

* Minimal refactoring is required
* Existing boundaries become spans
* Latency, errors, and bottlenecks become immediately visible

This makes the service ideal for demos, talks, workshops, and internal enablement sessions.

---

## 7. Dependencies & Environment

### Required Python Version

* Python 3.10+

### Core Dependencies

Create `requirements.txt` with:

```text
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
httpx==0.26.0
python-dotenv==1.0.0
```

### Development Dependencies (Optional)

Create `requirements-dev.txt` with:

```text
pytest==7.4.3
pytest-asyncio==0.23.3
httpx==0.26.0
black==23.12.1
ruff==0.1.11
```

### Environment Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 8. Data Models & Schemas

### 8.1 Request Models

**Location:** `app/schemas/request.py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class SearchRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=500, description="Search query")
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")

    @field_validator('q')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()

class ChaosConfig(BaseModel):
    model_failure_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    external_api_timeout_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    slow_search_rate: float = Field(default=0.2, ge=0.0, le=1.0)
    external_api_failure_rate: float = Field(default=0.05, ge=0.0, le=1.0)
```

### 8.2 Response Models

**Location:** `app/schemas/response.py`

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

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
    parsed_query: Dict[str, any] = Field(..., description="Parsed query details")
    results: List[SearchResult] = Field(..., description="Ranked search results")
    meta: ResponseMeta = Field(..., description="Response metadata")

class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Service health status")
    components: Dict[str, str] = Field(..., description="Component health checks")
    version: str = Field(default="1.0.0", description="Service version")

class ChaosConfigResponse(BaseModel):
    config: ChaosConfig = Field(..., description="Current chaos configuration")
    message: str = Field(..., description="Status message")
```

### 8.3 Internal Models

**Location:** `app/schemas/internal.py`

```python
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
```

---

## 9. Database Schema & Seed Data

### 9.1 SQLite Schema

**Location:** `app/data/schema.sql`

```sql
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    category TEXT NOT NULL,
    embedding TEXT NOT NULL,  -- JSON array of floats
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_title ON documents(title);

-- Full-text search support
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    doc_id UNINDEXED,
    title,
    text,
    content=documents,
    content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, doc_id, title, text)
    VALUES (new.rowid, new.doc_id, new.title, new.text);
END;

CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
    DELETE FROM documents_fts WHERE rowid = old.rowid;
END;

CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
    UPDATE documents_fts SET title = new.title, text = new.text
    WHERE rowid = old.rowid;
END;
```

### 9.2 Seed Data

**Location:** `app/data/seed_data.py`

Provide exactly 50 documents covering 5 categories (10 docs each):

**Categories:**
* `machine_learning` (10 docs)
* `data_science` (10 docs)
* `web_development` (10 docs)
* `cloud_computing` (10 docs)
* `cybersecurity` (10 docs)

**Document Generation Algorithm:**

```python
import json
import hashlib

CATEGORIES = {
    "machine_learning": [
        "neural networks", "deep learning", "supervised learning",
        "unsupervised learning", "reinforcement learning", "gradient descent",
        "backpropagation", "convolutional networks", "transformers", "model training"
    ],
    "data_science": [
        "data analysis", "statistical modeling", "data visualization",
        "pandas", "numpy", "exploratory analysis", "hypothesis testing",
        "regression analysis", "time series", "feature engineering"
    ],
    "web_development": [
        "javascript frameworks", "react", "vue", "angular", "REST APIs",
        "GraphQL", "web security", "responsive design", "progressive web apps",
        "server-side rendering"
    ],
    "cloud_computing": [
        "AWS services", "Azure cloud", "Google Cloud Platform", "kubernetes",
        "docker containers", "serverless architecture", "cloud storage",
        "load balancing", "auto scaling", "cloud security"
    ],
    "cybersecurity": [
        "network security", "encryption", "authentication", "authorization",
        "penetration testing", "vulnerability assessment", "security protocols",
        "firewalls", "intrusion detection", "security compliance"
    ]
}

def generate_seed_documents():
    """Generate deterministic seed documents"""
    documents = []
    doc_counter = 1

    for category, topics in CATEGORIES.items():
        for i, topic in enumerate(topics):
            doc_id = f"{category[:3].upper()}{doc_counter:03d}"

            # Generate deterministic embedding (8-dim for simplicity)
            seed_str = f"{category}_{topic}_{i}"
            hash_obj = hashlib.md5(seed_str.encode())
            hash_bytes = hash_obj.digest()
            embedding = [
                (hash_bytes[j] / 255.0) * 2 - 1  # Normalize to [-1, 1]
                for j in range(8)
            ]

            title = topic.title()
            text = f"This document covers {topic} in the context of {category.replace('_', ' ')}. " \
                   f"It provides comprehensive information about {topic} concepts, " \
                   f"best practices, and real-world applications. " \
                   f"Key aspects include implementation details, common patterns, and expert insights."

            documents.append({
                "doc_id": doc_id,
                "title": title,
                "text": text,
                "category": category,
                "embedding": json.dumps(embedding)
            })

            doc_counter += 1

    return documents
```

**Database Initialization:**

**Location:** `app/data/init_db.py`

```python
import sqlite3
import os
from pathlib import Path
from .seed_data import generate_seed_documents

DATABASE_PATH = Path(__file__).parent / "search.db"

def init_database():
    """Initialize database with schema and seed data"""
    # Remove existing database for clean slate
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Read and execute schema
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)

    # Insert seed data
    documents = generate_seed_documents()
    for doc in documents:
        cursor.execute(
            "INSERT INTO documents (doc_id, title, text, category, embedding) VALUES (?, ?, ?, ?, ?)",
            (doc["doc_id"], doc["title"], doc["text"], doc["category"], doc["embedding"])
        )

    conn.commit()
    conn.close()

    return DATABASE_PATH

if __name__ == "__main__":
    db_path = init_database()
    print(f"Database initialized at: {db_path}")
```

---

## 10. Configuration Specification

### 10.1 Environment Variables

**Location:** `.env` (create in project root, add to `.gitignore`)

```bash
# Application Settings
APP_NAME="Search & Recommendation Service"
APP_VERSION="1.0.0"
ENVIRONMENT="development"  # development, staging, production

# Server Settings
HOST="0.0.0.0"
PORT=8000
RELOAD=true  # Auto-reload on code changes (dev only)

# Database
DATABASE_PATH="app/data/search.db"

# External API Settings
WIKIPEDIA_API_URL="https://en.wikipedia.org/api/rest_v1"
WIKIPEDIA_TIMEOUT=5.0  # seconds
WIKIPEDIA_MAX_RETRIES=2

# Chaos Configuration (Default values)
CHAOS_MODEL_FAILURE_RATE=0.05
CHAOS_EXTERNAL_TIMEOUT_RATE=0.1
CHAOS_SLOW_SEARCH_RATE=0.2
CHAOS_EXTERNAL_FAILURE_RATE=0.05

# Performance Settings
SEARCH_SLOW_THRESHOLD_MS=500  # When chaos triggers, add this delay
MODEL_TIMEOUT_SECONDS=2.0

# Ranking Weights
WEIGHT_SEARCH=0.5
WEIGHT_RECOMMENDATION=0.3
WEIGHT_EXTERNAL=0.2

# Stopwords (comma-separated)
STOPWORDS="the,a,an,and,or,but,in,on,at,to,for,of,with,by,from,as,is,was,are,were,be,been"
```

### 10.2 Configuration Class

**Location:** `app/core/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # Application
    app_name: str = "Search & Recommendation Service"
    app_version: str = "1.0.0"
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # Database
    database_path: str = "app/data/search.db"

    # External API
    wikipedia_api_url: str = "https://en.wikipedia.org/api/rest_v1"
    wikipedia_timeout: float = 5.0
    wikipedia_max_retries: int = 2

    # Chaos
    chaos_model_failure_rate: float = 0.05
    chaos_external_timeout_rate: float = 0.1
    chaos_slow_search_rate: float = 0.2
    chaos_external_failure_rate: float = 0.05

    # Performance
    search_slow_threshold_ms: int = 500
    model_timeout_seconds: float = 2.0

    # Ranking
    weight_search: float = 0.5
    weight_recommendation: float = 0.3
    weight_external: float = 0.2

    # NLP
    stopwords: str = "the,a,an,and,or,but,in,on,at,to,for,of,with,by,from,as,is,was,are,were,be,been"

    @property
    def stopwords_list(self) -> List[str]:
        return [w.strip() for w in self.stopwords.split(',')]

# Global settings instance
settings = Settings()
```

---

## 11. Component Implementation Details

### 11.1 Query Parser

**Location:** `app/core/query_parser.py`

**Algorithm:**

```python
import re
from typing import List
from app.schemas.internal import ParsedQuery, QueryIntent
from app.core.config import settings

class QueryParser:
    def __init__(self):
        self.stopwords = set(settings.stopwords_list)

    def parse(self, query: str) -> ParsedQuery:
        """
        Parse and normalize search query

        Algorithm:
        1. Normalize: lowercase and strip
        2. Tokenize: split on whitespace and punctuation
        3. Remove stopwords
        4. Detect intent: if <= 2 tokens → discovery, else → search
        """
        # Normalize
        normalized = query.lower().strip()

        # Tokenize: split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', normalized)

        # Remove stopwords
        filtered_tokens = [t for t in tokens if t not in self.stopwords and len(t) > 1]

        # If no tokens remain after filtering, keep original tokens
        if not filtered_tokens:
            filtered_tokens = tokens

        # Detect intent
        intent = QueryIntent.DISCOVERY if len(filtered_tokens) <= 2 else QueryIntent.SEARCH

        return ParsedQuery(
            original=query,
            normalized=normalized,
            tokens=filtered_tokens,
            intent=intent,
            token_count=len(filtered_tokens)
        )
```

### 11.2 Search Index

**Location:** `app/search/index.py`

**Algorithm:**

```python
import sqlite3
import json
import time
import random
from typing import List
from app.schemas.internal import SearchIndexResult, ParsedQuery
from app.core.config import settings
from app.core.chaos import chaos_manager

class SearchIndex:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def search(self, parsed_query: ParsedQuery, limit: int = 10) -> List[SearchIndexResult]:
        """
        Search documents using SQLite FTS5

        Algorithm:
        1. Check chaos config for slow search injection
        2. Build FTS query from parsed tokens
        3. Execute FTS search
        4. Calculate base_score using BM25 rank (normalized)
        5. Count matching tokens for each result
        """
        # Chaos injection: slow search
        if chaos_manager.should_trigger_slow_search():
            time.sleep(settings.search_slow_threshold_ms / 1000.0)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build FTS query: OR all tokens together
        fts_query = ' OR '.join(parsed_query.tokens)

        # Execute FTS search
        cursor.execute("""
            SELECT
                d.doc_id,
                d.title,
                d.text,
                fts.rank as bm25_rank
            FROM documents_fts fts
            JOIN documents d ON d.rowid = fts.rowid
            WHERE documents_fts MATCH ?
            ORDER BY fts.rank
            LIMIT ?
        """, (fts_query, limit * 2))  # Fetch extra for diversity

        results = []
        for row in cursor.fetchall():
            # Calculate match count
            text_lower = (row['title'] + ' ' + row['text']).lower()
            match_count = sum(1 for token in parsed_query.tokens if token in text_lower)

            # Normalize BM25 rank to [0, 1] using sigmoid
            # BM25 rank is negative; closer to 0 is better
            base_score = 1.0 / (1.0 + abs(row['bm25_rank']))

            results.append(SearchIndexResult(
                doc_id=row['doc_id'],
                title=row['title'],
                text=row['text'][:200],  # Truncate to snippet
                base_score=base_score,
                match_count=match_count
            ))

        conn.close()

        # Limit to requested amount
        return results[:limit]
```

### 11.3 Feature Builder

**Location:** `app/recommendation/features.py`

**Algorithm:**

```python
import json
import sqlite3
from typing import List
from app.schemas.internal import ParsedQuery, SearchIndexResult, FeatureVector
from app.core.config import settings

CATEGORY_ENCODING = {
    "machine_learning": 0,
    "data_science": 1,
    "web_development": 2,
    "cloud_computing": 3,
    "cybersecurity": 4
}

class FeatureBuilder:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def build_features(
        self,
        parsed_query: ParsedQuery,
        doc: SearchIndexResult,
        user_id: str
    ) -> FeatureVector:
        """
        Build feature vector for ML model

        Features:
        - query_length: character count of original query
        - query_token_count: number of tokens
        - user_id_hash: stable hash of user_id (mod 1000)
        - doc_length: character count of document text
        - doc_category_encoded: integer encoding of category
        - query_doc_overlap: Jaccard similarity of query tokens and doc tokens
        - embedding_dot_product: dot product of query and doc embeddings
        """
        # Query features
        query_length = len(parsed_query.original)
        query_token_count = parsed_query.token_count

        # User feature
        user_id_hash = hash(user_id) % 1000

        # Document features
        doc_length = len(doc.text)

        # Get document category and embedding from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT category, embedding FROM documents WHERE doc_id = ?",
            (doc.doc_id,)
        )
        row = cursor.fetchone()
        conn.close()

        category = row[0] if row else "machine_learning"
        doc_embedding = json.loads(row[1]) if row else [0.0] * 8
        doc_category_encoded = CATEGORY_ENCODING.get(category, 0)

        # Query-doc overlap (Jaccard similarity)
        doc_tokens = set(doc.text.lower().split())
        query_tokens = set(parsed_query.tokens)
        intersection = len(query_tokens & doc_tokens)
        union = len(query_tokens | doc_tokens)
        query_doc_overlap = intersection / union if union > 0 else 0.0

        # Embedding similarity (generate query embedding on-the-fly)
        query_embedding = self._generate_query_embedding(parsed_query)
        embedding_dot_product = sum(
            q * d for q, d in zip(query_embedding, doc_embedding)
        )

        return FeatureVector(
            query_length=query_length,
            query_token_count=query_token_count,
            user_id_hash=user_id_hash,
            doc_length=doc_length,
            doc_category_encoded=doc_category_encoded,
            query_doc_overlap=query_doc_overlap,
            embedding_dot_product=embedding_dot_product
        )

    def _generate_query_embedding(self, parsed_query: ParsedQuery) -> List[float]:
        """
        Generate deterministic 8-dim embedding for query
        Uses hash of each token, combines with weighted average
        """
        if not parsed_query.tokens:
            return [0.0] * 8

        embeddings = []
        for token in parsed_query.tokens:
            token_hash = hash(token)
            embedding = [
                ((token_hash >> (i * 8)) & 0xFF) / 255.0 * 2 - 1
                for i in range(8)
            ]
            embeddings.append(embedding)

        # Average pooling
        avg_embedding = [
            sum(emb[i] for emb in embeddings) / len(embeddings)
            for i in range(8)
        ]

        return avg_embedding
```

### 11.4 Mock ML Model

**Location:** `app/recommendation/model.py`

**Algorithm:**

```python
import random
import time
import math
from app.schemas.internal import FeatureVector, ModelPrediction
from app.recommendation.errors import ModelError, ModelTimeoutError
from app.core.chaos import chaos_manager
from app.core.config import settings

class MockMLModel:
    """
    Mock ML model that simulates realistic ML inference behavior

    Scoring Algorithm (deterministic with controlled randomness):
    1. Compute weighted sum of normalized features
    2. Apply sigmoid transformation for [0, 1] range
    3. Add small random noise based on feature hash (deterministic per input)
    4. Chaos injection: occasionally fail or timeout
    """

    def __init__(self):
        self.version = "mock_v1"
        self.feature_weights = {
            'query_doc_overlap': 0.30,
            'embedding_dot_product': 0.25,
            'query_token_count': 0.15,
            'doc_category_encoded': 0.10,
            'match_quality': 0.20  # Derived feature
        }

    def predict(self, features: FeatureVector) -> ModelPrediction:
        """
        Generate prediction from features

        Raises:
            ModelError: Random inference failure (5% default)
            ModelTimeoutError: Simulated timeout (rare)
        """
        # Chaos injection: model failure
        if chaos_manager.should_trigger_model_failure():
            raise ModelError("Model inference failed: simulated error")

        # Simulate inference time (10-50ms normally, with rare timeouts)
        inference_time = random.uniform(0.010, 0.050)
        if random.random() < 0.01:  # 1% chance of slow inference
            inference_time = settings.model_timeout_seconds * 0.8
        time.sleep(inference_time)

        # Feature engineering: derive match_quality
        match_quality = (features.query_doc_overlap +
                        max(0, features.embedding_dot_product)) / 2.0

        # Compute weighted score
        score = (
            self.feature_weights['query_doc_overlap'] * features.query_doc_overlap +
            self.feature_weights['embedding_dot_product'] * max(0, features.embedding_dot_product) +
            self.feature_weights['query_token_count'] * min(features.query_token_count / 10.0, 1.0) +
            self.feature_weights['doc_category_encoded'] * (features.doc_category_encoded / 4.0) +
            self.feature_weights['match_quality'] * match_quality
        )

        # Apply sigmoid for [0, 1] range
        score = 1.0 / (1.0 + math.exp(-5 * (score - 0.5)))

        # Add deterministic noise based on feature hash
        feature_hash = hash((
            features.query_length,
            features.query_token_count,
            features.user_id_hash,
            features.doc_length
        ))
        random.seed(feature_hash)
        noise = random.uniform(-0.05, 0.05)
        random.seed()  # Reset seed

        score = max(0.0, min(1.0, score + noise))

        # Confidence: higher for extreme scores
        confidence = abs(score - 0.5) * 2.0

        return ModelPrediction(
            score=score,
            confidence=confidence,
            model_version=self.version
        )
```

**Location:** `app/recommendation/errors.py`

```python
class ModelError(Exception):
    """Raised when model inference fails"""
    pass

class ModelTimeoutError(Exception):
    """Raised when model inference times out"""
    pass
```

### 11.5 Wikipedia External API

**Location:** `app/external/wikipedia.py`

**Algorithm:**

```python
import httpx
import asyncio
from typing import Optional
from app.schemas.internal import ExternalSignal, ParsedQuery
from app.core.config import settings
from app.core.chaos import chaos_manager

class WikipediaClient:
    def __init__(self):
        self.base_url = settings.wikipedia_api_url
        self.timeout = settings.wikipedia_timeout
        self.max_retries = settings.wikipedia_max_retries

    async def get_signal(self, parsed_query: ParsedQuery) -> Optional[ExternalSignal]:
        """
        Fetch external signal from Wikipedia API

        Algorithm:
        1. Extract primary topic (first non-stopword token)
        2. Call Wikipedia page summary API
        3. Chaos injection: simulate timeout or failure
        4. Calculate relevance score based on extract length and view count proxy
        5. Return signal or None if failed
        """
        # Chaos injection: external API failure
        if chaos_manager.should_trigger_external_failure():
            raise httpx.HTTPError("Simulated external API failure")

        # Chaos injection: timeout
        if chaos_manager.should_trigger_external_timeout():
            await asyncio.sleep(settings.wikipedia_timeout + 1)
            raise httpx.TimeoutException("Simulated timeout")

        # Extract topic (use first meaningful token)
        topic = parsed_query.tokens[0] if parsed_query.tokens else "search"

        url = f"{self.base_url}/page/summary/{topic}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=self.timeout)

                if response.status_code == 200:
                    data = response.json()

                    # Extract signals
                    description = data.get('extract', '')
                    description_length = len(description)

                    # Relevance score based on extract length
                    # Longer extracts (up to 500 chars) indicate better match
                    relevance_score = min(description_length / 500.0, 1.0)

                    # Popularity proxy (if available in response)
                    popularity_proxy = None
                    if 'pageviews' in data:
                        popularity_proxy = min(data['pageviews'] / 10000.0, 1.0)

                    return ExternalSignal(
                        source="wikipedia",
                        relevance_score=relevance_score,
                        description_length=description_length,
                        popularity_proxy=popularity_proxy
                    )
                else:
                    return None

        except (httpx.TimeoutException, httpx.HTTPError) as e:
            # Log error (in production, use proper logging)
            print(f"Wikipedia API error: {e}")
            return None
```

### 11.6 Ranker

**Location:** `app/core/ranker.py`

**Algorithm:**

```python
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
```

### 11.7 Chaos Manager

**Location:** `app/core/chaos.py`

**Algorithm:**

```python
import random
from app.schemas.request import ChaosConfig

class ChaosManager:
    """
    Centralized chaos injection management

    Uses pseudo-random triggers based on configured failure rates
    Each trigger is independent per request
    """

    def __init__(self):
        self.config = ChaosConfig()

    def update_config(self, new_config: ChaosConfig):
        """Update chaos configuration at runtime"""
        self.config = new_config

    def get_config(self) -> ChaosConfig:
        """Get current chaos configuration"""
        return self.config

    def should_trigger_model_failure(self) -> bool:
        """Determine if model should fail this request"""
        return random.random() < self.config.model_failure_rate

    def should_trigger_external_timeout(self) -> bool:
        """Determine if external API should timeout this request"""
        return random.random() < self.config.external_api_timeout_rate

    def should_trigger_slow_search(self) -> bool:
        """Determine if search should be slow this request"""
        return random.random() < self.config.slow_search_rate

    def should_trigger_external_failure(self) -> bool:
        """Determine if external API should fail this request"""
        return random.random() < self.config.external_api_failure_rate

# Global chaos manager instance
chaos_manager = ChaosManager()
```

---

## 12. Error Handling & HTTP Status Codes

### 12.1 Error Response Model

**Location:** `app/schemas/response.py` (add to existing file)

```python
class ErrorDetail(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, any]] = Field(None, description="Additional error context")

class ErrorResponse(BaseModel):
    detail: ErrorDetail
```

### 12.2 HTTP Status Code Mapping

| Scenario | Status Code | Error Type | Message Example |
|----------|-------------|------------|-----------------|
| Empty query after validation | 400 | `validation_error` | "Query cannot be empty or whitespace only" |
| Query too long (>500 chars) | 400 | `validation_error` | "Query exceeds maximum length of 500 characters" |
| Invalid limit parameter | 400 | `validation_error` | "Limit must be between 1 and 100" |
| Missing required parameter | 422 | `request_validation_error` | "Field required: user_id" |
| Model inference failure | 500 | `model_error` | "Model inference failed" |
| External API timeout | 504 | `gateway_timeout` | "External API request timed out" |
| Database connection error | 500 | `database_error` | "Failed to connect to search index" |
| Unknown internal error | 500 | `internal_error` | "An unexpected error occurred" |

### 12.3 Exception Handlers

**Location:** `app/api/search.py` (in route handlers)

```python
from fastapi import HTTPException
from app.recommendation.errors import ModelError, ModelTimeoutError

# Example usage in search endpoint
try:
    prediction = model.predict(features)
except ModelError as e:
    # Log but continue without recommendation score
    prediction = None
except ModelTimeoutError as e:
    # Log but continue
    prediction = None
```

---

## 13. Application Lifecycle

### 13.1 Startup Sequence

**Location:** `app/main.py`

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.data.init_db import init_database
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize database
    logger.info("Initializing database...")
    db_path = init_database()
    logger.info(f"Database ready at: {db_path}")

    # Log configuration
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Chaos config: model_failure={settings.chaos_model_failure_rate}, "
                f"external_timeout={settings.chaos_external_timeout_rate}")

    yield

    # Shutdown
    logger.info("Shutting down service...")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# Include routers
from app.api import search
app.include_router(search.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
```

### 13.2 Graceful Shutdown

Uvicorn handles graceful shutdown automatically:
* Completes in-flight requests
* Closes database connections
* No explicit cleanup needed for this simple service

---

## 14. Complete API Route Implementation

### 14.1 Search Endpoint

**Location:** `app/api/search.py`

```python
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
```

---

## 15. Running the Service

### 15.1 Initial Setup

```bash
# 1. Create project directory
mkdir search-recommendation-service
cd search-recommendation-service

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (copy from section 10.1)

# 5. Initialize database
python -m app.data.init_db
```

### 15.2 Start Server

```bash
# Development mode (auto-reload)
python app/main.py

# Or using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 15.3 Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Search request
curl "http://localhost:8000/search?q=machine+learning&user_id=user123&limit=5"

# Get chaos config
curl http://localhost:8000/chaos/config

# Update chaos config
curl -X POST http://localhost:8000/chaos/config \
  -H "Content-Type: application/json" \
  -d '{"model_failure_rate": 0.2, "external_api_timeout_rate": 0.3}'
```

### 15.4 Interactive API Docs

FastAPI provides automatic interactive documentation:
* Swagger UI: `http://localhost:8000/docs`
* ReDoc: `http://localhost:8000/redoc`

---

## 16. Testing Strategy

### 16.1 Unit Tests (Optional)

**Location:** `tests/test_query_parser.py`

```python
import pytest
from app.core.query_parser import QueryParser
from app.schemas.internal import QueryIntent

def test_query_parser_basic():
    parser = QueryParser()
    result = parser.parse("Machine Learning")

    assert result.normalized == "machine learning"
    assert "machine" in result.tokens
    assert "learning" in result.tokens
    assert result.intent == QueryIntent.SEARCH

def test_query_parser_stopwords():
    parser = QueryParser()
    result = parser.parse("the quick brown fox")

    # "the" should be removed as stopword
    assert "the" not in result.tokens
    assert "quick" in result.tokens
```

### 16.2 Integration Test

**Location:** `tests/test_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_endpoint():
    response = client.get("/search?q=python&user_id=test123&limit=5")
    assert response.status_code == 200

    data = response.json()
    assert "query" in data
    assert "results" in data
    assert len(data["results"]) <= 5

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

---

## 18. Expected Behavior Examples

### Example 1: Normal Search Request

**Request:**
```http
GET /search?q=neural+networks&user_id=alice&limit=3
```

**Expected Response:**
```json
{
  "query": "neural networks",
  "parsed_query": {
    "normalized": "neural networks",
    "tokens": ["neural", "networks"],
    "intent": "discovery",
    "token_count": 2
  },
  "results": [
    {
      "doc_id": "MAC001",
      "title": "Neural Networks",
      "text": "This document covers neural networks in the context of machine learning...",
      "score": 0.87,
      "explanations": {
        "search": 0.92,
        "recommendation": 0.78,
        "external": 0.65
      }
    }
  ],
  "meta": {
    "latency_ms": 245,
    "model_version": "mock_v1",
    "components_called": ["query_parser", "search_index", "recommendation_engine", "wikipedia_api", "ranker"]
  }
}
```

### Example 2: Chaos Injection - Model Failure

With `model_failure_rate: 0.5` (50% failure rate):

**Request:**
```http
GET /search?q=python&user_id=bob&limit=5
```

**Expected Behavior:**
* Some documents will have `recommendation: 0.0` in explanations
* Response still succeeds (graceful degradation)
* Latency may vary
* `components_called` may not include "recommendation_engine" if all predictions failed

### Example 3: Update Chaos Config

**Request:**
```http
POST /chaos/config
Content-Type: application/json

{
  "model_failure_rate": 0.8,
  "external_api_timeout_rate": 0.5,
  "slow_search_rate": 0.3,
  "external_api_failure_rate": 0.2
}
```

**Expected Response:**
```json
{
  "config": {
    "model_failure_rate": 0.8,
    "external_api_timeout_rate": 0.5,
    "slow_search_rate": 0.3,
    "external_api_failure_rate": 0.2
  },
  "message": "Chaos configuration updated successfully"
}
```