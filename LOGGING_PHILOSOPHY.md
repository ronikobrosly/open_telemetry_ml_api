# Logging Philosophy & Guidelines

This document explains the logging approach used in this microservice and how it complements OpenTelemetry tracing.

## Core Principle

**Logs capture events and milestones. Traces capture detailed context.**

- **Logs** = What happened, when it happened, and why it matters
- **Spans** = How it happened, with full technical details

## Logging Strategy

### What Gets Logged

✅ **DO log these events:**
- Request ingress and completion (INFO)
- Chaos events that affect behavior (WARNING)
- Actual errors and failures (WARNING/ERROR)
- Configuration changes (INFO)

❌ **DON'T log these:**
- Individual processing steps (already in spans)
- Detailed technical metrics (already in span attributes)
- Success cases for internal operations (clutters logs)
- Duplicate information already in spans

### Log Levels

| Level | Purpose | Examples |
|-------|---------|----------|
| **INFO** | Request lifecycle events | "Search request received", "Search request completed" |
| **WARNING** | Recoverable issues & chaos events | "Chaos: slow search", "Model prediction failed" |
| **ERROR** | Critical failures | (Currently handled via span exceptions) |
| **DEBUG** | Optional detailed flow | "Query parsed", "Search completed" (off by default) |

### Log Structure

All logs include:
1. **Automatic context** (from OpenTelemetry):
   - `trace_id` - Links to distributed trace
   - `span_id` - Links to specific span
   - `service.name` - Service identifier

2. **Minimal essential fields** (in `extra`):
   - `user_id` - For filtering user journeys
   - Event-specific minimal context

## Current Logging by Component

### Search Endpoint (`app/api/search.py`)

```python
# Request start (INFO)
logger.info("Search request received", extra={
    "user_id": user_id,
    "query": q
})

# Request completion (INFO)
logger.info("Search request completed", extra={
    "user_id": user_id,
    "latency_ms": latency_ms,
    "result_count": len(ranked_results)
})

# Model prediction failure (WARNING)
logger.warning("Model prediction failed", extra={
    "user_id": user_id,
    "doc_id": doc.doc_id
})

# External API failure (WARNING)
logger.warning("Wikipedia API failed", extra={
    "user_id": user_id,
    "error_type": type(e).__name__
})

# Chaos config update (INFO)
logger.info("Chaos configuration updated", extra={
    "model_failure_rate": config.model_failure_rate,
    "slow_search_rate": config.slow_search_rate
})
```

### Search Index (`app/search/index.py`)

```python
# Chaos event (WARNING)
logger.warning("Chaos: slow search", extra={
    "delay_ms": settings.search_slow_threshold_ms
})
```

### ML Model (`app/recommendation/model.py`)

```python
# Chaos event (WARNING)
logger.warning("Chaos: model failure")
```

### Wikipedia Client (`app/external/wikipedia.py`)

```python
# Chaos events (WARNING)
logger.warning("Chaos: external API failure")
logger.warning("Chaos: external API timeout")
```

### Ranker (`app/core/ranker.py`)

No logging - all details captured in spans.

## How to Use Logs & Traces Together

### Scenario 1: Investigating a Slow Request

1. **Start with logs** filtered by user or time:
   ```
   user_id = "mock_user_1234567"
   latency_ms > 1000
   ```

2. **Click the trace_id** in the log to jump to the full trace

3. **Analyze the trace** to see:
   - Which component was slow (span durations)
   - All the technical details (100+ span attributes)
   - Sub-operation timing

### Scenario 2: Tracking Chaos Events

1. **Filter logs** for chaos warnings:
   ```
   level = "WARNING" AND message CONTAINS "Chaos:"
   ```

2. **See which chaos events fired** (slow search, model failure, etc.)

3. **Jump to traces** to see:
   - How chaos affected the request flow
   - Actual performance impact
   - Recovery mechanisms

### Scenario 3: Following a User Journey

1. **Filter logs by user_id**:
   ```
   user_id = "mock_user_1234567"
   ```

2. **See all requests** made by that user (request received + completed)

3. **Click any trace_id** to see:
   - Query details
   - Which documents were recommended
   - Feature values and scores
   - Component performance

## What's in Spans vs Logs

### Logs Contain:
- Event name/message
- Timestamp
- Log level
- `user_id` (for filtering)
- Minimal event-specific context
- Automatic: `trace_id`, `span_id`, `service.name`

### Spans Contain:
- Component name
- Duration
- Parent/child relationships
- ~100 detailed attributes:
  - Query parsing details
  - Search results and scores
  - ML features and predictions
  - External API responses
  - Ranking configuration and results
  - Error details

## Benefits of This Approach

### 1. Clean, Scannable Logs
- Not overwhelmed with technical details
- Easy to spot important events
- Fast to filter and search

### 2. Rich Traces
- Full technical context for debugging
- Drill down into any request
- Understand complex interactions

### 3. Seamless Correlation
- Every log has `trace_id` and `span_id`
- Click once to jump from log → trace
- No manual correlation needed

### 4. Cost Effective
- Logs are compact (low storage cost)
- Traces have retention policies
- Get detail when you need it

### 5. Demo Friendly
- Logs show the story (what happened)
- Traces show the details (how it happened)
- Easy to explain to audiences

## Example: Full Request Flow

**Logs (what you see):**
```
[INFO] Search request received | user_id=mock_user_1234567, query="machine learning"
[WARNING] Model prediction failed | user_id=mock_user_1234567, doc_id=MAC003
[INFO] Search request completed | user_id=mock_user_1234567, latency_ms=487, result_count=10
```

**Trace (what you can drill into):**
```
Root Span: /search
├─ Attributes: user_id, query, limit, chaos config, latency, components...
├─ Query Parser
│  └─ Attributes: tokens, normalized query, intent, stopwords removed...
├─ Search Index
│  └─ Attributes: fts_query, results count, scores (min/max/avg), top docs...
├─ Recommendation Engine
│  ├─ Model Prediction (MAC001) - Success
│  │  └─ Attributes: all features, scores, confidence, inference time...
│  ├─ Model Prediction (MAC002) - Success
│  │  └─ Attributes: all features, scores, confidence, inference time...
│  └─ Model Prediction (MAC003) - FAILED
│     └─ Attributes: all features, error details...
├─ Wikipedia API
│  └─ Attributes: topic, url, response, relevance score...
└─ Ranker
   └─ Attributes: weights, scores, coverage, top results...
```

**Result:**
- Logs give you the high-level narrative
- Traces give you forensic-level detail
- Both are automatically linked via trace_id

## Adjusting Log Verbosity

### Production (Recommended)
```python
setup_logging(level=logging.INFO)
```
- Shows: Request lifecycle, warnings, errors
- Hides: DEBUG logs (query parsed, search completed, etc.)

### Development/Debugging
```python
setup_logging(level=logging.DEBUG)
```
- Shows: Everything including component completions
- Useful for development and troubleshooting

### Configuration Location
Change log level in `app/main.py`:
```python
setup_logging(level=logging.INFO)  # or logging.DEBUG
```

## Summary

| Need | Use |
|------|-----|
| "What requests happened?" | Filter logs by user_id or time |
| "Did anything go wrong?" | Filter logs by level=WARNING |
| "What did this request do?" | Logs show high-level flow |
| "Why was this request slow?" | Click trace_id → analyze spans |
| "What were the feature values?" | Span attributes |
| "How did ranking work?" | Span attributes |
| "What caused this error?" | Span exceptions + attributes |

**The key insight:** Logs are your index. Traces are your encyclopedia. Together, they provide complete observability with minimal noise.
