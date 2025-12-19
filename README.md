# Search & Recommendation Service

A demo-friendly FastAPI microservice designed to showcase the value of OpenTelemetry (OTel). This service combines full-text search, ML-based recommendations, and external API signals to rank documents, with built-in chaos engineering capabilities.

## Overview

This service demonstrates:
- **Full-text search** using SQLite FTS5 with BM25 ranking
- **Mock ML recommendation engine** with realistic failure modes
- **External API integration** (Wikipedia REST API)
- **Score fusion** from multiple signals (search, ML, external)
- **Chaos engineering** for observability testing
- **Clean component boundaries** ideal for distributed tracing

## Prerequisites

- **Python 3.10+**
- **uv** package manager (recommended) or pip
- **curl** for testing (or any HTTP client)

## Quick Start

### 1. Installation

```bash
# Clone or navigate to the project directory
cd otel_demo

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 2. Run the Server

```bash
# Set PYTHONPATH and start the server
PYTHONPATH=/home/ronik/otel_demo python app/main.py
```

Or using uvicorn directly:

```bash
PYTHONPATH=/home/ronik/otel_demo uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see output like:

```
INFO:app.main:Starting Search & Recommendation Service v1.0.0
INFO:app.main:Initializing database...
INFO:app.main:Database ready at: /home/ronik/otel_demo/app/data/search.db
INFO:app.main:Environment: development
INFO:app.main:Chaos config: model_failure=0.05, external_timeout=0.1
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The database is automatically initialized with 50 seed documents on startup.

## API Endpoints

### Health Check

Check if the service is running:

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "ml_model": "healthy",
    "external_api": "healthy"
  },
  "version": "1.0.0"
}
```

### Search Documents

Search for documents with ML recommendations and external signals:

```bash
curl "http://localhost:8000/search?q=machine+learning&user_id=alice&limit=3"
```

**Parameters:**
- `q` (required): Search query (1-500 characters)
- `user_id` (required): User identifier (1-100 characters)
- `limit` (optional): Maximum results to return (1-100, default: 10)

**Example Response:**
```json
{
  "query": "machine learning",
  "parsed_query": {
    "normalized": "machine learning",
    "tokens": ["machine", "learning"],
    "intent": "discovery",
    "token_count": 2
  },
  "results": [
    {
      "doc_id": "MAC004",
      "title": "Unsupervised Learning",
      "text": "This document covers unsupervised learning...",
      "score": 0.183,
      "explanations": {
        "search": 0.217,
        "recommendation": 0.249,
        "external": 0.0
      }
    }
  ],
  "meta": {
    "latency_ms": 219,
    "model_version": "mock_v1",
    "components_called": [
      "query_parser",
      "search_index",
      "recommendation_engine",
      "ranker"
    ],
    "cache_hit": false
  }
}
```

**Score Explanations:**
- `search`: BM25 full-text search score (weight: 50%)
- `recommendation`: ML model prediction (weight: 30%)
- `external`: Wikipedia relevance signal (weight: 20%)
- `score`: Final weighted combination

### More Search Examples

**Web development query:**
```bash
curl "http://localhost:8000/search?q=react+javascript&user_id=bob&limit=5"
```

**Cloud computing query:**
```bash
curl "http://localhost:8000/search?q=kubernetes+docker&user_id=charlie&limit=3"
```

**Cybersecurity query:**
```bash
curl "http://localhost:8000/search?q=encryption+security&user_id=dave&limit=5"
```

## Chaos Engineering

The service includes configurable chaos injection to simulate realistic production failures.

### Get Current Chaos Configuration

```bash
curl http://localhost:8000/chaos/config
```

**Response:**
```json
{
  "config": {
    "model_failure_rate": 0.05,
    "external_api_timeout_rate": 0.1,
    "slow_search_rate": 0.2,
    "external_api_failure_rate": 0.05
  },
  "message": "Current chaos configuration"
}
```

### Update Chaos Configuration

Inject failures to test observability:

```bash
curl -X POST http://localhost:8000/chaos/config \
  -H "Content-Type: application/json" \
  -d '{
    "model_failure_rate": 0.8,
    "external_api_timeout_rate": 0.5,
    "slow_search_rate": 0.3,
    "external_api_failure_rate": 0.2
  }'
```

**Chaos Parameters:**
- `model_failure_rate` (0.0-1.0): Probability ML model inference fails
- `external_api_timeout_rate` (0.0-1.0): Probability external API times out
- `slow_search_rate` (0.0-1.0): Probability search is artificially slowed (500ms)
- `external_api_failure_rate` (0.0-1.0): Probability external API fails

### Testing Chaos Injection

**Example 1: High Model Failure Rate**

```bash
# Enable high failure rate
curl -X POST http://localhost:8000/chaos/config \
  -H "Content-Type: application/json" \
  -d '{"model_failure_rate": 0.8, "external_api_timeout_rate": 0.1, "slow_search_rate": 0.2, "external_api_failure_rate": 0.05}'

# Run multiple searches to see failures
for i in {1..5}; do
  echo "Request $i:"
  curl -s "http://localhost:8000/search?q=machine+learning&user_id=test$i&limit=3" | \
    python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"  Latency: {data['meta']['latency_ms']}ms, Components: {data['meta']['components_called']}\")"
done
```

**What to observe:**
- Some results will have `recommendation: 0.0` (model failed)
- `components_called` may not include `"recommendation_engine"`
- Service continues to work (graceful degradation)

**Example 2: Slow Search Simulation**

```bash
# Enable slow search
curl -X POST http://localhost:8000/chaos/config \
  -H "Content-Type: application/json" \
  -d '{"model_failure_rate": 0.05, "external_api_timeout_rate": 0.1, "slow_search_rate": 1.0, "external_api_failure_rate": 0.05}'

# Search will now take ~500ms longer
curl "http://localhost:8000/search?q=cloud+computing&user_id=alice&limit=3"
```

**What to observe:**
- `latency_ms` increases from ~200ms to ~700ms
- All other components work normally

**Example 3: Reset to Normal**

```bash
# Reset to default low failure rates
curl -X POST http://localhost:8000/chaos/config \
  -H "Content-Type: application/json" \
  -d '{"model_failure_rate": 0.05, "external_api_timeout_rate": 0.1, "slow_search_rate": 0.2, "external_api_failure_rate": 0.05}'
```

## Interactive API Documentation

FastAPI provides auto-generated interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Use these to explore endpoints, see request/response schemas, and make test requests directly from your browser.

## Document Categories

The service contains 50 seed documents across 5 categories:

| Category | Document Count | Example Topics |
|----------|---------------|----------------|
| Machine Learning | 10 | neural networks, deep learning, supervised learning |
| Data Science | 10 | pandas, numpy, data visualization |
| Web Development | 10 | react, vue, REST APIs, GraphQL |
| Cloud Computing | 10 | AWS, kubernetes, docker, serverless |
| Cybersecurity | 10 | encryption, authentication, penetration testing |

## Ranking Algorithm

Final scores are calculated using weighted fusion:

```
final_score = 0.5 × search_score + 0.3 × recommendation_score + 0.2 × external_score
```

These weights can be configured in `.env`:
```bash
WEIGHT_SEARCH=0.5
WEIGHT_RECOMMENDATION=0.3
WEIGHT_EXTERNAL=0.2
```

## Project Structure

```
otel_demo/
├── app/
│   ├── api/            # API route handlers
│   ├── core/           # Core business logic (parser, ranker, chaos)
│   ├── data/           # Database schema, seed data, initialization
│   ├── external/       # External API clients (Wikipedia)
│   ├── recommendation/ # ML model, feature builder, errors
│   ├── schemas/        # Pydantic models (request, response, internal)
│   ├── search/         # Search index implementation
│   └── main.py         # FastAPI application entry point
├── .env                # Environment configuration
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Configuration

Key environment variables in `.env`:

```bash
# Chaos Configuration
CHAOS_MODEL_FAILURE_RATE=0.05
CHAOS_EXTERNAL_TIMEOUT_RATE=0.1
CHAOS_SLOW_SEARCH_RATE=0.2
CHAOS_EXTERNAL_FAILURE_RATE=0.05

# Ranking Weights
WEIGHT_SEARCH=0.5
WEIGHT_RECOMMENDATION=0.3
WEIGHT_EXTERNAL=0.2

# Performance
SEARCH_SLOW_THRESHOLD_MS=500
MODEL_TIMEOUT_SECONDS=2.0

# External API
WIKIPEDIA_API_URL="https://en.wikipedia.org/api/rest_v1"
WIKIPEDIA_TIMEOUT=5.0
```

## Troubleshooting

**Issue: Module not found errors**

Make sure to set PYTHONPATH:
```bash
export PYTHONPATH=/path/to/otel_demo
python app/main.py
```

**Issue: Port already in use**

Change the port in `.env`:
```bash
PORT=8001
```

**Issue: Database locked**

Stop the server and delete the database:
```bash
rm app/data/search.db
# Restart server - database will be recreated
```

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## Next Steps: OpenTelemetry Integration

This service is designed to be instrumented with OpenTelemetry. Future enhancements:

1. **Automatic Instrumentation**: Add FastAPI, SQLite, and HTTP client instrumentation
2. **Custom Spans**: Instrument each component (parser, search, model, ranker)
3. **Metrics**: Track request rates, latencies, error rates, model prediction scores
4. **Logs**: Structured logging with trace context
5. **Export**: Send telemetry to Jaeger, Prometheus, or other backends

The clean component boundaries and chaos engineering make this ideal for demonstrating:
- Distributed tracing across microservice boundaries
- Error tracking and alerting
- Performance bottleneck identification
- ML model observability
- Graceful degradation patterns