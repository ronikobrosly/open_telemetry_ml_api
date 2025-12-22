# Logging Enhancements for SigNoz Trace Correlation

This document describes the comprehensive logging improvements made to the microservice to enable better log-trace correlation in SigNoz.

## Overview

Enhanced structured logging has been added throughout the application with rich contextual information. All logs include relevant metadata in the `extra` field, making them easy to filter, search, and correlate with traces in SigNoz.

## Key Logging Levels Used

- **INFO**: Normal operation milestones (request received, component completed, etc.)
- **WARNING**: Chaos events, partial failures, API errors
- **ERROR**: Critical failures that impact the request
- **DEBUG**: Detailed technical information (feature values, scores, etc.)

## Logging Enhancements by Component

### 1. Search Endpoint (`app/api/search.py`)

#### Request Ingress
```python
logger.info("Search request received", extra={
    "user_id": user_id,
    "query": q,
    "query_length": len(q),
    "limit": limit,
    "endpoint": "search"
})
```

#### Query Parsing
```python
logger.info("Query parsed successfully", extra={
    "user_id": user_id,
    "original_query": q,
    "normalized_query": parsed_query.normalized,
    "tokens": parsed_query.tokens,
    "token_count": parsed_query.token_count,
    "intent": parsed_query.intent.value,
    "parse_duration_ms": component_duration
})
```

#### Search Index Results
```python
logger.info("Search index query completed", extra={
    "user_id": user_id,
    "query": q,
    "result_count": len(search_results),
    "search_duration_ms": component_duration,
    "top_doc_ids": [doc.doc_id for doc in search_results[:3]],
    "top_scores": [round(doc.base_score, 3) for doc in search_results[:3]]
})
```

#### ML Prediction Batch
```python
# Batch start
logger.info("Starting ML prediction batch", extra={
    "user_id": user_id,
    "query": q,
    "document_count": len(search_results),
    "model_version": ml_model.version
})

# Individual predictions (DEBUG level)
logger.debug("ML prediction successful", extra={
    "user_id": user_id,
    "doc_id": doc.doc_id,
    "prediction_score": round(prediction.score, 3),
    "confidence": round(prediction.confidence, 3),
    "inference_duration_ms": round(prediction_duration, 2)
})

# Prediction failures
logger.warning("Model prediction failed", extra={
    "user_id": user_id,
    "doc_id": doc.doc_id,
    "doc_title": doc.title,
    "error": str(e),
    "error_type": "ModelError",
    "inference_duration_ms": round(prediction_duration, 2)
})

# Batch completion
logger.info("ML prediction batch completed", extra={
    "user_id": user_id,
    "query": q,
    "total_documents": len(search_results),
    "successful_predictions": successful_predictions,
    "failed_predictions": failed_predictions,
    "success_rate": round(successful_predictions / len(search_results) * 100, 1)
})
```

#### Wikipedia API
```python
# API call initiation
logger.info("Fetching external signal from Wikipedia", extra={
    "user_id": user_id,
    "query": q,
    "topic": parsed_query.tokens[0]
})

# Successful response
logger.info("Wikipedia API call successful", extra={
    "user_id": user_id,
    "query": q,
    "relevance_score": round(external_signal.relevance_score, 3),
    "description_length": external_signal.description_length,
    "source": "wikipedia"
})

# No data returned
logger.warning("Wikipedia API returned no data", extra={
    "user_id": user_id,
    "query": q,
    "topic": parsed_query.tokens[0]
})

# API failure
logger.error("Wikipedia API call failed", extra={
    "user_id": user_id,
    "query": q,
    "error": str(e),
    "error_type": type(e).__name__
})
```

#### Ranking
```python
logger.info("Ranking completed", extra={
    "user_id": user_id,
    "query": q,
    "result_count": len(ranked_results),
    "ranking_duration_ms": round(component_duration, 2),
    "top_3_doc_ids": [r.doc_id for r in ranked_results[:3]],
    "top_3_final_scores": [round(r.score, 3) for r in ranked_results[:3]]
})
```

#### Request Completion
```python
logger.info("Search request completed", extra={
    "user_id": user_id,
    "query": q,
    "total_latency_ms": latency_ms,
    "result_count": len(ranked_results),
    "components_called": components_called,
    "model_predictions_successful": successful_predictions,
    "model_predictions_failed": failed_predictions,
    "external_signal_available": external_signal is not None
})
```

#### Chaos Configuration Updates
```python
logger.info("Chaos configuration update requested", extra={
    "model_failure_rate": config.model_failure_rate,
    "external_timeout_rate": config.external_api_timeout_rate,
    "slow_search_rate": config.slow_search_rate,
    "external_failure_rate": config.external_api_failure_rate
})
```

### 2. Search Index (`app/search/index.py`)

#### Chaos Event - Slow Search
```python
logger.warning("Chaos event triggered: slow search", extra={
    "event_type": "slow_search",
    "delay_ms": settings.search_slow_threshold_ms,
    "tokens": parsed_query.tokens
})
```

#### Search Execution
```python
logger.debug("Executing FTS search", extra={
    "tokens": parsed_query.tokens,
    "token_count": parsed_query.token_count,
    "limit": limit
})
```

#### Search Results
```python
logger.debug("Search index results retrieved", extra={
    "tokens": parsed_query.tokens,
    "results_found": len(final_results),
    "fts_query": fts_query,
    "avg_score": round(sum(r.base_score for r in final_results) / len(final_results), 3)
})
```

### 3. ML Model (`app/recommendation/model.py`)

#### Chaos Event - Model Failure
```python
logger.warning("Chaos event triggered: model failure", extra={
    "event_type": "model_failure",
    "model_version": self.version,
    "feature_hash": hash((features.query_length, features.user_id_hash))
})
```

#### Successful Prediction
```python
logger.debug("Model prediction generated", extra={
    "model_version": self.version,
    "prediction_score": round(score, 3),
    "confidence": round(confidence, 3),
    "inference_time_ms": round(actual_inference_time_ms, 2),
    "feature_overlap": round(features.query_doc_overlap, 3),
    "embedding_similarity": round(features.embedding_dot_product, 3),
    "match_quality": round(match_quality, 3)
})
```

### 4. Wikipedia Client (`app/external/wikipedia.py`)

#### Chaos Event - External Failure
```python
logger.warning("Chaos event triggered: external API failure", extra={
    "event_type": "external_failure",
    "api": "wikipedia",
    "topic": parsed_query.tokens[0]
})
```

#### Chaos Event - Timeout
```python
logger.warning("Chaos event triggered: external API timeout", extra={
    "event_type": "external_timeout",
    "api": "wikipedia",
    "timeout_seconds": settings.wikipedia_timeout + 1,
    "topic": parsed_query.tokens[0]
})
```

#### API Call Initiation
```python
logger.debug("Calling Wikipedia API", extra={
    "api": "wikipedia",
    "topic": topic,
    "url": url,
    "timeout": self.timeout
})
```

#### Successful API Response
```python
logger.info("Wikipedia API response processed", extra={
    "api": "wikipedia",
    "topic": topic,
    "status_code": response.status_code,
    "api_duration_ms": round(api_duration_ms, 2),
    "relevance_score": round(relevance_score, 3),
    "description_length": description_length,
    "has_popularity_data": popularity_proxy is not None
})
```

#### Non-200 Status
```python
logger.warning("Wikipedia API returned non-200 status", extra={
    "api": "wikipedia",
    "topic": topic,
    "status_code": response.status_code,
    "api_duration_ms": round(api_duration_ms, 2)
})
```

### 5. Ranker (`app/core/ranker.py`)

#### Ranking Process Start
```python
logger.debug("Starting ranking process", extra={
    "num_documents": len(search_results),
    "num_predictions": len(model_predictions),
    "has_external_signal": external_signal is not None,
    "external_score": round(external_score, 3),
    "weights": {
        "search": self.weight_search,
        "recommendation": self.weight_recommendation,
        "external": self.weight_external
    }
})
```

#### Ranking Completion
```python
logger.debug("Ranking completed", extra={
    "num_results": len(ranked_results),
    "top_doc_id": ranked_results[0].doc_id,
    "top_final_score": round(ranked_results[0].score, 3),
    "score_range": {
        "min": round(min(r.score for r in ranked_results), 3),
        "max": round(max(r.score for r in ranked_results), 3),
        "avg": round(sum(r.score for r in ranked_results) / len(ranked_results), 3)
    }
})
```

## Common Log Fields

All logs include these common contextual fields where applicable:

- **user_id**: User making the request (for filtering by user)
- **query**: The search query
- **doc_id**: Document identifier
- **component durations**: Time spent in each component (*_duration_ms)
- **scores**: Prediction scores, relevance scores, etc.
- **error information**: Error type, message, stack traces
- **chaos events**: Event type, configuration values

## Using Logs in SigNoz

### 1. Filtering by User
```
user_id = "mock_user_1234567"
```

### 2. Finding Failed Predictions
```
level = "WARNING" AND error_type = "ModelError"
```

### 3. Tracking Slow Requests
```
total_latency_ms > 1000
```

### 4. Chaos Event Analysis
```
event_type = "slow_search" OR event_type = "model_failure"
```

### 5. Component Performance
```
search_duration_ms > 500
```

### 6. Correlation with Traces
- All logs automatically include trace_id and span_id from OpenTelemetry context
- Click on any log in SigNoz to jump to its associated trace
- Use user_id and query fields to correlate across multiple requests

## Log Levels by Environment

To change log verbosity, update the logging setup in `app/core/logging.py`:

- **Production**: INFO level (captures milestones and issues)
- **Staging/Demo**: INFO level (same as production for realistic demos)
- **Development**: DEBUG level (captures all details)

## Benefits for Demo

These enhanced logs enable you to:

1. **Track user journeys**: Follow a specific user through multiple requests
2. **Identify bottlenecks**: See which component is slow for each request
3. **Debug ML failures**: Understand why predictions failed with feature context
4. **Analyze chaos impact**: Correlate chaos events with performance degradation
5. **Validate external APIs**: Track Wikipedia API success rates and latencies
6. **Score debugging**: See how ranking combines different signals
7. **Request flow visualization**: Understand the complete request lifecycle

## Example SigNoz Queries

```
# All requests for a specific user
user_id = "mock_user_1234567"

# Failed ML predictions with context
level = "WARNING" AND message CONTAINS "prediction failed"

# Slow searches triggered by chaos
event_type = "slow_search"

# Successful Wikipedia API calls
message CONTAINS "Wikipedia API call successful"

# High-latency requests
total_latency_ms > 1000

# Requests with no external signal
external_signal_available = false
```

Each log message is now rich with context, making it easy to understand what happened, why it happened, and how it relates to the distributed trace!
