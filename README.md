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
cd open_telemetry_ml_api

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 2. Run the Server

```bash
# Set PYTHONPATH and start the server
PYTHONPATH=/home/ronik/Desktop/open_telemetry_ml_api python app/main.py
```

Or using uvicorn directly:

```bash
PYTHONPATH=/home/ronik/Desktop/open_telemetry_ml_api uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see output like:

```
INFO:app.main:Starting Search & Recommendation Service v1.0.0
INFO:app.main:Initializing database...
INFO:app.main:Database ready at: /home/ronik/open_telemetry_ml_api/app/data/search.db
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
open_telemetry_ml_api/
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
export PYTHONPATH=/path/to/open_telemetry_ml_api
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

---

# OpenTelemetry Instrumentation Plan

This service is designed to showcase comprehensive OpenTelemetry instrumentation for ML systems with SigNoz.

## Implementation Overview

**Approach**: Hybrid auto-instrumentation (60%) + manual instrumentation (40%)
- **Auto-instrumentation**: FastAPI HTTP, httpx external calls, SQLite queries
- **Manual instrumentation**: ML model inference, feature building, ranking, chaos events

**Total effort**: 3 days, ~559 lines of code across 16 files (4 new, 12 modified)

## Span Hierarchy

```
ROOT: GET /search (auto-instrumented by FastAPI)
├── query_parser.parse (manual)
├── search_index.search (manual parent)
│   └── SQLite: SELECT FROM documents_fts (auto)
├── recommendation_engine (manual parent for batch)
│   ├── feature_builder.build_features[doc=MAC001] (manual)
│   │   └── SQLite: SELECT FROM documents (auto)
│   ├── model.predict[doc=MAC001] (manual)
│   ├── feature_builder.build_features[doc=MAC002] (manual)
│   ├── model.predict[doc=MAC002] (manual)
│   └── ... (per-document spans)
├── wikipedia_client.get_signal (manual parent)
│   └── GET https://en.wikipedia.org/... (auto by httpx)
└── ranker.rank (manual)
```

## Dependencies

Add to `requirements.txt`:

```text
# OpenTelemetry Core
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0

# Auto-instrumentation
opentelemetry-instrumentation-fastapi==0.43b0
opentelemetry-instrumentation-httpx==0.43b0
opentelemetry-instrumentation-sqlite3==0.43b0

# OTLP Exporter for SigNoz
opentelemetry-exporter-otlp==1.22.0

# Bootstrap utilities
opentelemetry-distro==0.43b0
opentelemetry-instrumentation==0.43b0
```

## Environment Configuration

Add to `.env`:

```bash
# OpenTelemetry Configuration
OTEL_SERVICE_NAME="search-recommendation-service"
OTEL_SERVICE_VERSION="1.0.0"
OTEL_DEPLOYMENT_ENVIRONMENT="development"

# SigNoz OTLP Endpoint
OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"

# Traces configuration
OTEL_TRACES_SAMPLER="always_on"
OTEL_TRACES_SAMPLER_ARG="1.0"

# Metrics configuration
OTEL_METRICS_EXPORTER="otlp"
OTEL_METRIC_EXPORT_INTERVAL="60000"
```

---

## Using with SigNoz

SigNoz is an open-source observability platform that provides a complete solution for traces, metrics, and logs. This section guides you through setting up SigNoz and connecting this instrumented application.

### Installing SigNoz

SigNoz can be installed in multiple ways. Choose the method that best fits your environment.

#### Option 1: Docker Compose (Recommended for Local Development)

**Prerequisites:**
- Docker 20.10.0 or higher
- Docker Compose v2.0.0 or higher
- 4GB of RAM minimum

**Install SigNoz:**

```bash
# Clone SigNoz repository
git clone -b main https://github.com/SigNoz/signoz.git
cd signoz/deploy/

# Run installation script
./install.sh
```

This will:
- Download and start all SigNoz components (ClickHouse, Query Service, Frontend, OTel Collector)
- Expose the UI on `http://localhost:8080`
- Expose OTLP gRPC endpoint on `localhost:4317`
- Expose OTLP HTTP endpoint on `localhost:4318`

**Verify installation:**
```bash
# Check all containers are running
docker ps

# You should see containers for:
# - signoz-otel-collector
# - signoz-query-service
# - signoz-frontend
# - signoz-clickhouse
# - signoz-alertmanager
# - signoz-zookeeper
```

**Access SigNoz UI:**
Open your browser to `http://localhost:8080`

**Stop SigNoz:**
```bash
cd ~/Desktop/signoz/
docker compose -f docker/docker-compose.yaml stop
```

**Start SigNoz again:**
```bash
cd ~/Desktop/signoz/
docker compose -f docker/docker-compose.yaml start
```

#### Option 2: Kubernetes (For Production/Staging)

**Prerequisites:**
- Kubernetes 1.23+
- kubectl configured
- Helm 3.8+

**Install via Helm:**

```bash
# Add SigNoz Helm repo
helm repo add signoz https://charts.signoz.io
helm repo update

# Create namespace
kubectl create namespace platform

# Install SigNoz
helm install signoz signoz/signoz -n platform
```

**Get the SigNoz UI URL:**
```bash
kubectl --namespace platform get services
```

**Configure port forwarding (for local access):**
```bash
kubectl --namespace platform port-forward svc/signoz-frontend 3301:3301
kubectl --namespace platform port-forward svc/signoz-otel-collector 4317:4317
```

### Connecting Your Application to SigNoz

#### Step 1: Verify SigNoz is Running

**Check SigNoz health:**
```bash
# For Docker installation
curl http://localhost:8080/api/v1/health
```

**Verify OTLP endpoint:**
```bash
# gRPC endpoint (our default)
nc -zv localhost 4317

# HTTP endpoint (alternative)
nc -zv localhost 4318
```

#### Step 2: Configure Application Environment

Your `.env` is already configured for local SigNoz:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
```

**For remote SigNoz or Kubernetes:**
Update the endpoint in `.env`:
```bash
OTEL_EXPORTER_OTLP_ENDPOINT="http://<signoz-host>:4317"
```

#### Step 3: Install Dependencies (if not already done)

```bash
pip install -r requirements.txt
```

This includes all OpenTelemetry packages needed to send data to SigNoz.

#### Step 4: Start Your Application

```bash
# From project root
PYTHONPATH=~/Desktop/open_telemetry_ml_api python app/main.py
```

**Look for these log messages indicating successful OTel initialization:**
```json
{"timestamp": "...", "level": "INFO", "message": "OpenTelemetry initialized", "service_name": "search-recommendation-service", "endpoint": "http://localhost:4317"}
{"timestamp": "...", "level": "INFO", "message": "Auto-instrumentation applied"}
```

#### Step 5: Generate Test Traffic

```bash
# Make a few search requests
curl "http://localhost:8000/search?q=machine+learning&user_id=alice&limit=3"
curl "http://localhost:8000/search?q=python+programming&user_id=bob&limit=5"
curl "http://localhost:8000/search?q=kubernetes+docker&user_id=charlie&limit=3"
```

**Wait 10-30 seconds** for data to appear in SigNoz (batching delay).

### Exploring Data in SigNoz

#### Viewing Traces

1. **Open SigNoz UI:** `http://localhost:3301`
2. **Navigate to Services:** Click "Services" in the left sidebar
3. **Find your service:** Look for `search-recommendation-service`
4. **Click on service name** to see service overview:
   - Request rate (requests/sec)
   - Error rate (%)
   - P99, P95, P50 latencies
   - Apdex score

5. **View Traces:**
   - Click "Traces" tab
   - You'll see a list of all traces
   - Each trace represents one `/search` request

6. **Inspect a Trace:**
   - Click on any trace to see the detailed view
   - You'll see the span hierarchy:
     ```
     GET /search [200 OK, 245ms]
     ├── query_parser.parse [2ms]
     ├── search_index.search [45ms]
     │   └── SQLite: SELECT [42ms]
     ├── recommendation_engine [120ms]
     │   ├── model.predict[doc=MAC001] [15ms]
     │   └── model.predict[doc=MAC002] [14ms]
     ├── wikipedia_client.get_signal [65ms]
     └── ranker.rank [8ms]
     ```

7. **View Span Attributes:**
   - Click on any span (e.g., `model.predict`)
   - See attributes like:
     - `model.score`: 0.87
     - `model.confidence`: 0.74
     - `doc_id`: MAC001
     - `model.version`: mock_v1

#### Viewing Metrics

1. **Navigate to Dashboards:** Click "Dashboards" in left sidebar
2. **Create New Dashboard:** Click "+ New Dashboard"
3. **Add Panel** and configure queries:

**Request Rate Panel:**
- Metric: `http_requests_total`
- Visualization: Time series
- Group by: `status_code`

**Model Performance Panel:**
- Metric: `model_predictions_total`
- Visualization: Pie chart
- Group by: `status` (success/failure)

**Latency Panel:**
- Metric: `http_request_duration`
- Visualization: Time series
- Aggregation: P95, P99
- Group by: `route`

**Chaos Events Panel:**
- Metric: `chaos_events_total`
- Visualization: Bar chart
- Group by: `event_type`

#### Viewing Logs (with Trace Correlation)

1. **Navigate to Logs:** Click "Logs" in left sidebar
2. **Search by trace ID:**
   - Copy a `trace_id` from a trace
   - Paste into logs search: `trace_id:<your-trace-id>`
   - See all logs for that specific request

3. **Filter by error level:**
   - Search: `level:WARNING` or `level:ERROR`
   - See all error logs with their trace context

4. **Jump from Trace to Logs:**
   - In trace view, click "View Logs" button
   - Automatically filters logs for that trace

### Step-by-Step Demo Walkthrough

This walkthrough demonstrates all OpenTelemetry features in SigNoz.

#### Demo 1: Normal Request Flow

**Objective:** See complete distributed trace across all components.

```bash
# Make a clean request
curl "http://localhost:8000/search?q=machine+learning&user_id=demo1&limit=3"
```

**In SigNoz:**
1. Go to Traces → Filter by `user_id=demo1`
2. Click on the trace
3. **Observe:**
   - All 6 component spans visible
   - Each span has timing information
   - Query parser shows `query.token_count=2`, `query.intent=discovery`
   - Search index shows `search.result_count=3`
   - Each `model.predict` span shows `model.score` and `model.confidence`
   - Wikipedia span shows `external.topic` and `external.relevance_score`

#### Demo 2: Chaos Engineering - Model Failures

**Objective:** Show how OTel captures ML model failures.

```bash
# Enable high model failure rate
curl -X POST http://localhost:8000/chaos/config \
  -H "Content-Type: application/json" \
  -d '{"model_failure_rate": 0.8, "external_api_timeout_rate": 0.1, "slow_search_rate": 0.2, "external_api_failure_rate": 0.05}'

# Generate requests (some will fail)
for i in {1..10}; do
  curl "http://localhost:8000/search?q=python&user_id=chaos_demo_$i&limit=5"
done
```

**In SigNoz:**
1. Go to Traces → Filter by `user_id` contains `chaos_demo`
2. Look for traces with red/error indicators
3. Click on a trace with errors
4. **Observe:**
   - Some `model.predict` spans are marked as ERROR (red)
   - Click on error span → see `chaos.triggered=true`
   - See `chaos.event_type=model_failure`
   - Exception details in span events
   - Request still returns 200 OK (graceful degradation!)

5. Go to Metrics → View `chaos_events_total`
   - See spike in chaos events
   - Breakdown by `event_type`

#### Demo 3: Slow Search Detection

**Objective:** Identify performance bottlenecks.

```bash
# Enable slow search
curl -X POST http://localhost:8000/chaos/config \
  -H "Content-Type: application/json" \
  -d '{"model_failure_rate": 0.05, "external_api_timeout_rate": 0.1, "slow_search_rate": 1.0, "external_api_failure_rate": 0.05}'

# Make request (will be slow)
curl "http://localhost:8000/search?q=kubernetes&user_id=slow_demo&limit=3"
```

**In SigNoz:**
1. Go to Traces → Filter by `user_id=slow_demo`
2. Click on trace
3. **Observe:**
   - `search_index.search` span takes ~500ms longer
   - Span has `chaos.triggered=true` attribute
   - Total request latency increased
   - Flamegraph view shows search as bottleneck

#### Demo 4: Log-Trace Correlation

**Objective:** Correlate logs with traces for debugging.

```bash
# Reset chaos to default
curl -X POST http://localhost:8000/chaos/config \
  -H "Content-Type: application/json" \
  -d '{"model_failure_rate": 0.5, "external_api_timeout_rate": 0.1, "slow_search_rate": 0.2, "external_api_failure_rate": 0.1}'

# Generate requests that will produce errors
for i in {1..5}; do
  curl "http://localhost:8000/search?q=testing&user_id=log_demo_$i&limit=3"
done
```

**In SigNoz:**
1. Go to Traces → Find a trace with errors
2. Copy the `trace_id` (e.g., `a1b2c3d4e5f6g7h8`)
3. Go to Logs → Search: `trace_id:a1b2c3d4e5f6g7h8`
4. **Observe:**
   - All logs for this specific request
   - Logs show detailed error messages
   - Each log has `trace_id` and `span_id`
   - Can see "Model prediction failed" warnings with doc_id
   - Timeline correlates with trace spans

5. **Reverse flow:** In Logs, click "View Trace" button
   - Jumps directly to the trace
   - See full context of what happened

#### Demo 5: Service Health Monitoring

**Objective:** Monitor overall service health and SLIs.

```bash
# Generate steady traffic
for i in {1..50}; do
  curl "http://localhost:8000/search?q=monitoring&user_id=health_demo_$i&limit=3"
  sleep 1
done
```

**In SigNoz:**
1. Go to Services → `search-recommendation-service`
2. **Service Overview Dashboard:**
   - **Request Rate:** See ~1 req/sec
   - **Error Rate:** Should be low (< 5% if defaults)
   - **P99 Latency:** Typically 300-500ms
   - **P95 Latency:** Typically 200-400ms

3. Go to Dashboards → Create "SLI Dashboard"
4. **Add panels:**
   - Availability SLI: `sum(http_requests_total{status_code=~"2.."}) / sum(http_requests_total)` × 100
   - Latency SLI: P95 of `http_request_duration` < 500ms threshold
   - Model Reliability: `sum(model_predictions_total{status="success"}) / sum(model_predictions_total)` × 100

### Troubleshooting

#### Traces Not Appearing in SigNoz

**Problem:** Made requests but no traces in SigNoz.

**Solutions:**

1. **Check SigNoz is running:**
   ```bash
   docker ps | grep signoz
   # Should see 6 containers running
   ```

2. **Verify OTLP collector is accessible:**
   ```bash
   nc -zv localhost 4317
   # Should show: Connection to localhost 4317 port [tcp/*] succeeded!
   ```

3. **Check application logs for OTel errors:**
   ```bash
   # Look for OpenTelemetry initialization messages
   # Should see: "OpenTelemetry initialized"
   ```

4. **Verify environment variables:**
   ```bash
   python -c "from app.core.config import settings; print(settings.otel_exporter_endpoint)"
   # Should print: http://localhost:4317
   ```

5. **Check SigNoz collector logs:**
   ```bash
   docker logs signoz-otel-collector
   # Look for errors about receiving data
   ```

6. **Wait longer:** Spans are batched every 30 seconds, so wait at least 1 minute after making requests.

#### Metrics Not Showing Up

**Problem:** Traces work but metrics don't appear.

**Solutions:**

1. **Check metric export interval:**
   - Metrics export every 60 seconds by default
   - Wait at least 2 minutes after request

2. **Verify in dashboard:**
   - Go to Dashboard → Add Panel
   - Try query: `http_requests_total`
   - If no suggestions appear, metrics aren't being received

3. **Check OTel collector config:**
   ```bash
   # Verify metrics pipeline is enabled in SigNoz
   docker exec signoz-otel-collector cat /etc/otel-collector-config.yaml
   ```

#### Connection Refused Error

**Problem:** `connection refused` when starting app.

**Solutions:**

1. **Wrong endpoint in .env:**
   ```bash
   # Should be gRPC port 4317, not HTTP 4318
   OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
   ```

2. **SigNoz not running:**
   ```bash
   cd signoz/deploy/
   docker compose -f docker/clickhouse-setup/docker-compose.yaml start
   ```

3. **Firewall blocking port:**
   ```bash
   sudo ufw allow 4317
   ```

#### High Memory Usage

**Problem:** SigNoz using too much memory.

**Solutions:**

1. **Reduce retention period:**
   - Edit `signoz/deploy/docker/clickhouse-setup/docker-compose.yaml`
   - Set lower TTL for ClickHouse tables

2. **Enable sampling in production:**
   ```bash
   # In .env, change from 100% to 10%
   OTEL_TRACES_SAMPLER="parentbased_traceidratio"
   OTEL_TRACES_SAMPLER_ARG="0.1"
   ```

3. **Increase batch size to reduce overhead:**
   - Edit `app/core/telemetry.py`
   - Increase `max_queue_size` and `max_export_batch_size`

### Best Practices for Production

1. **Use Sampling:**
   ```bash
   OTEL_TRACES_SAMPLER="parentbased_traceidratio"
   OTEL_TRACES_SAMPLER_ARG="0.1"  # 10% sampling
   ```

2. **Set Resource Limits:**
   - Configure memory limits for OTel collector
   - Monitor collector resource usage

3. **Use Persistent Storage:**
   - Configure ClickHouse volumes for data persistence
   - Regular backups of SigNoz data

4. **Set Up Alerts:**
   - Alert on high error rates (> 5%)
   - Alert on P99 latency spikes
   - Alert on model failure rate > 10%

5. **Use Service Tags:**
   - Add environment tags (dev/staging/prod)
   - Add version tags for deployments
   - Group services by team/domain

### Additional Resources

- **SigNoz Documentation:** https://signoz.io/docs/
- **OpenTelemetry Python Docs:** https://opentelemetry.io/docs/instrumentation/python/
- **SigNoz Community:** https://signoz.io/slack
- **Troubleshooting Guide:** `INSTRUMENTATION_COMPLETE.md` in this repo

---

## Implementation Phases

### Phase 1: Foundation
1. Add OTel packages to requirements.txt
2. Update .env with SigNoz configuration
3. Create `app/core/telemetry.py` - OTel initialization
4. Create `app/core/logging.py` - Structured logging with trace context
5. Update `app/main.py` to initialize OTel before app creation

### Phase 2: Auto-Instrumentation
1. Apply FastAPI auto-instrumentation (HTTP spans)
2. Apply httpx instrumentation (Wikipedia API spans)
3. Apply SQLite3 instrumentation (database query spans)

### Phase 3: Manual Spans
1. Create `app/core/tracing.py` with decorator pattern
2. Instrument main orchestration in `app/api/search.py`
3. Instrument query parser, search index, ranker

### Phase 4: ML Observability
1. Instrument `app/recommendation/model.py` with per-document spans
2. Add model score, confidence, inference time attributes
3. Instrument feature builder

### Phase 5: Chaos & Error Handling
1. Add chaos event recording to spans
2. Record exceptions with full context
3. Replace print() with structured logging

### Phase 6: Metrics
1. Create `app/core/metrics.py`
2. Add counters (requests, predictions, chaos events)
3. Add histograms (latencies, scores)
4. Add gauges (chaos configuration)

## Expected Outcomes

### Normal Request Trace in SigNoz
```
GET /search [200 OK, 245ms]
├── query_parser.parse [2ms]
├── search_index.search [45ms]
│   └── SQLite: SELECT [42ms]
├── recommendation_engine [120ms]
│   ├── model.predict[MAC001] [15ms] score=0.87 confidence=0.74
│   └── model.predict[MAC002] [14ms] score=0.82 confidence=0.65
├── wikipedia_client.get_signal [65ms]
└── ranker.rank [8ms]
```

### Request with Chaos
```
GET /search [200 OK, 189ms]
├── search_index.search [150ms] ⚠️ chaos: slow_search
├── recommendation_engine [25ms]
│   ├── model.predict[MAC001] ❌ ERROR: model_failure
│   └── model.predict[MAC002] ✅ OK
└── wikipedia_client.get_signal ❌ ERROR: timeout
```

### Key Metrics in SigNoz
- **Request Rate**: http.requests.total by status_code
- **Latency**: http.request.duration P50/P95/P99
- **Model Performance**: model.predictions.total (success vs failure)
- **Chaos Events**: chaos.events.total by event_type
- **External API**: external.api.calls.total by status

### Structured Logs with Trace Context
```json
{
  "timestamp": "2025-12-18T10:30:45.123Z",
  "level": "WARNING",
  "logger": "app.recommendation.model",
  "message": "Model prediction failed",
  "trace_id": "a1b2c3d4e5f6g7h8",
  "span_id": "i9j0k1l2",
  "doc_id": "MAC001",
  "error": "Model inference failed: simulated error"
}
```

## Key Design Decisions

**Per-Document ML Spans**: Each document's prediction gets its own span to isolate failures and measure individual inference times.

**BatchSpanProcessor**: Production-ready span batching (max_queue_size=2048, max_export_batch_size=512) for performance.

**Always-On Sampling**: 100% sampling for demo to capture rare chaos events. Use 10% sampling in production.

**Hybrid Instrumentation**: Auto-instrumentation for infrastructure (HTTP, DB, external calls), manual for business logic (ML, ranking).

