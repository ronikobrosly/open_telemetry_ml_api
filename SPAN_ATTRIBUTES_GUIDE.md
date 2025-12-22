# Comprehensive Span Attributes Guide

This document catalogs all the span attributes added to the OpenTelemetry traces throughout the microservice. These attributes make traces highly searchable and analyzable in SigNoz.

## Root Span Attributes (`/search` endpoint)

The root span for each search request includes comprehensive context about the entire request lifecycle.

### Request Context
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `user_id` | string | User making the request | `"mock_user_1234567"` |
| `query` | string | Original search query | `"machine learning"` |
| `limit` | int | Maximum results requested | `10` |
| `endpoint` | string | API endpoint called | `"/search"` |
| `service.name` | string | Service identifier | `"search-recommendation-service"` |

### Chaos Configuration
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `chaos.model_failure_rate` | float | ML model failure probability | `0.05` |
| `chaos.external_timeout_rate` | float | External API timeout probability | `0.1` |
| `chaos.slow_search_rate` | float | Slow search probability | `0.2` |
| `chaos.external_failure_rate` | float | External API failure probability | `0.05` |

### Response Summary
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `response.total_latency_ms` | int | Total request duration | `245` |
| `response.result_count` | int | Number of results returned | `10` |
| `response.components_called` | string | Comma-separated component list | `"query_parser,search_index,recommendation_engine,wikipedia_api,ranker"` |
| `response.components_count` | int | Number of components invoked | `5` |
| `response.top_doc_id` | string | Document ID of top result | `"MAC001"` |
| `response.top_final_score` | float | Final score of top result | `0.873` |

### ML Prediction Summary
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `ml.predictions_successful` | int | Successful ML predictions | `8` |
| `ml.predictions_failed` | int | Failed ML predictions | `2` |
| `ml.prediction_success_rate` | float | Success rate percentage | `80.0` |

### External API Summary
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `external.signal_available` | bool | Whether external signal was obtained | `true` |

---

## Query Parser Span (`query_parser.parse`)

### Input Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `query.original` | string | Original query string | `"Machine Learning"` |
| `query.length` | int | Character count of original query | `17` |

### Processing Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `query.normalized` | string | Lowercased and trimmed query | `"machine learning"` |
| `query.raw_token_count` | int | Token count before stopword removal | `3` |
| `query.stopwords_removed` | int | Number of stopwords filtered | `1` |
| `query.fallback_to_raw_tokens` | bool | Whether stopword filtering was reversed | `false` |

### Output Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `query.final_token_count` | int | Final token count | `2` |
| `query.tokens` | string | Comma-separated tokens | `"machine,learning"` |
| `query.intent` | string | Detected query intent | `"discovery"` |

---

## Search Index Span (`search_index.search`)

### Input Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `search.limit` | int | Maximum results to return | `10` |
| `search.query_tokens` | string | Comma-separated query tokens | `"machine,learning"` |
| `search.token_count` | int | Number of query tokens | `2` |
| `search.query_intent` | string | Query intent classification | `"discovery"` |
| `search.fts_query` | string | Full-text search query constructed | `"machine OR learning"` |

### Chaos Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `chaos.triggered` | bool | Whether chaos was injected | `true` |
| `chaos.event_type` | string | Type of chaos event | `"slow_search"` |

### Result Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `search.results_found` | int | Number of results returned | `10` |
| `search.results_before_limit` | int | Results before limiting | `15` |
| `search.avg_base_score` | float | Average BM25 score | `0.756` |
| `search.max_base_score` | float | Maximum BM25 score | `0.923` |
| `search.min_base_score` | float | Minimum BM25 score | `0.612` |
| `search.top_doc_id` | string | Top document ID | `"MAC001"` |
| `search.top_doc_title` | string | Top document title | `"Neural Networks"` |
| `search.top_doc_ids` | string | Top 3 document IDs | `"MAC001,MAC002,DAT003"` |

---

## ML Model Prediction Span (`model.predict`)

### Model Configuration
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `model.version` | string | Model version identifier | `"mock_v1"` |

### Feature Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `features.query_length` | int | Query character count | `17` |
| `features.query_token_count` | int | Query token count | `2` |
| `features.user_id_hash` | int | Hashed user ID (for cohort analysis) | `567` |
| `features.doc_length` | int | Document character count | `342` |
| `features.doc_category_encoded` | int | Encoded document category | `0` |
| `features.query_doc_overlap` | float | Jaccard similarity | `0.667` |
| `features.embedding_dot_product` | float | Embedding similarity | `0.423` |
| `features.match_quality` | float | Derived feature (overlap + embedding)/2 | `0.545` |

### Chaos Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `chaos.triggered` | bool | Whether chaos was injected | `true` |
| `chaos.event_type` | string | Type of chaos event | `"model_failure"` |

### Prediction Results
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `model.inference_time_ms` | float | Inference duration | `23.45` |
| `model.prediction_score` | float | Final prediction score | `0.782` |
| `model.prediction_confidence` | float | Confidence in prediction | `0.564` |
| `model.raw_score_before_sigmoid` | float | Score before sigmoid transformation | `0.645` |

---

## Wikipedia External API Span (`wikipedia_client.get_signal`)

### Configuration Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `external.api` | string | External API name | `"wikipedia"` |
| `external.base_url` | string | API base URL | `"https://en.wikipedia.org/api/rest_v1"` |
| `external.timeout_config` | float | Configured timeout in seconds | `5.0` |
| `external.max_retries` | int | Maximum retry attempts | `2` |

### Request Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `external.query_tokens` | string | Comma-separated query tokens | `"machine,learning"` |
| `external.query_intent` | string | Query intent | `"discovery"` |
| `external.topic` | string | Wikipedia topic searched | `"machine"` |
| `external.url` | string | Full API URL called | `"https://en.wikipedia.org/api/rest_v1/page/summary/machine"` |

### Chaos Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `chaos.triggered` | bool | Whether chaos was injected | `true` |
| `chaos.event_type` | string | Type of chaos event | `"external_timeout"` or `"external_failure"` |

### Success Response Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `external.status` | string | Request outcome | `"success"` or `"error"` |
| `external.http_status_code` | int | HTTP response code | `200` |
| `external.api_duration_ms` | float | API call duration | `123.45` |
| `external.relevance_score` | float | Calculated relevance score | `0.845` |
| `external.description_length` | int | Wikipedia extract length | `423` |
| `external.has_popularity_data` | bool | Whether pageview data available | `true` |
| `external.popularity_score` | float | Normalized popularity score | `0.234` |
| `external.page_title` | string | Wikipedia page title | `"Machine learning"` |
| `external.page_type` | string | Type of Wikipedia page | `"standard"` |

### Error Response Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `external.status` | string | Request outcome | `"error"` |
| `external.http_status_code` | int | HTTP error code | `404` |
| `external.error_reason` | string | Error classification | `"non_200_status"` |
| `external.error_type` | string | Exception type | `"TimeoutException"` |
| `external.error_message` | string | Error description | `"Connection timeout"` |

---

## Ranker Span (`ranker.rank`)

### Configuration Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `ranking.weight_search` | float | Weight for search score | `0.5` |
| `ranking.weight_recommendation` | float | Weight for ML score | `0.3` |
| `ranking.weight_external` | float | Weight for external score | `0.2` |

### Input Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `ranking.num_input_documents` | int | Documents to rank | `10` |
| `ranking.num_predictions_available` | int | ML predictions available | `8` |
| `ranking.has_external_signal` | bool | External signal available | `true` |
| `ranking.external_score` | float | External signal score | `0.845` |
| `ranking.external_source` | string | External signal source | `"wikipedia"` |

### Output Attributes
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `ranking.num_output_results` | int | Final ranked results | `10` |
| `ranking.final_score_min` | float | Minimum final score | `0.523` |
| `ranking.final_score_max` | float | Maximum final score | `0.891` |
| `ranking.final_score_avg` | float | Average final score | `0.702` |
| `ranking.top_doc_id` | string | Top document ID | `"MAC001"` |
| `ranking.top_doc_title` | string | Top document title | `"Neural Networks"` |
| `ranking.top_final_score` | float | Top final combined score | `0.891` |
| `ranking.top_3_doc_ids` | string | Top 3 document IDs | `"MAC001,MAC002,DAT003"` |

### Score Component Analysis (Top Result)
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `ranking.top_search_score` | float | Search component of top result | `0.923` |
| `ranking.top_recommendation_score` | float | ML component of top result | `0.782` |
| `ranking.top_external_score` | float | External component of top result | `0.845` |

### Coverage Metrics
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `ranking.prediction_coverage` | float | % of docs with ML predictions | `0.8` |
| `ranking.docs_with_predictions` | int | Count of docs with predictions | `8` |

---

## Using Span Attributes in SigNoz

### Example Queries

**Find requests from a specific user:**
```
user_id = "mock_user_1234567"
```

**Find slow requests:**
```
response.total_latency_ms > 1000
```

**Find requests with high ML failure rate:**
```
ml.prediction_success_rate < 50
```

**Find chaos events:**
```
chaos.triggered = true
```

**Find specific chaos types:**
```
chaos.event_type = "model_failure"
chaos.event_type = "slow_search"
chaos.event_type = "external_timeout"
```

**Find requests with no external signal:**
```
external.signal_available = false
```

**Find high-quality matches:**
```
features.query_doc_overlap > 0.8
```

**Find requests by query intent:**
```
query.intent = "discovery"
query.intent = "search"
```

**Find low-confidence predictions:**
```
model.prediction_confidence < 0.3
```

**Filter by document category:**
```
features.doc_category_encoded = 0  # machine_learning
features.doc_category_encoded = 1  # data_science
```

**Find Wikipedia API errors:**
```
external.status = "error"
external.http_status_code != 200
```

**Analyze ranking behavior:**
```
ranking.prediction_coverage < 0.5  # Less than half docs have predictions
ranking.top_final_score > 0.9     # Very high confidence results
```

### Advanced Filtering

**Complex conditions:**
```
user_id = "mock_user_1234567" AND
response.total_latency_ms > 500 AND
ml.prediction_success_rate < 80
```

**Grouping and aggregation:**
- Group by `chaos.event_type` to see distribution of chaos events
- Group by `query.intent` to analyze discovery vs search patterns
- Group by `features.doc_category_encoded` to see category performance
- Aggregate `response.total_latency_ms` by `ml.prediction_success_rate` to correlate latency with ML health

### Correlation Analysis

**Trace → Logs:**
All logs automatically include `trace_id` and `span_id`, so you can:
1. Click on any span in SigNoz
2. View correlated logs for that specific span
3. See structured log data with all the extra fields

**Metrics → Traces:**
Use span attributes to:
1. Filter traces by specific conditions
2. Identify outliers or problematic patterns
3. Drill down into specific user journeys
4. Analyze component-level performance

## Span Attribute Naming Conventions

All attributes follow a hierarchical naming pattern:

- `query.*` - Query parsing and normalization
- `search.*` - Search index operations
- `features.*` - ML feature engineering
- `model.*` - ML model inference
- `external.*` - External API calls
- `ranking.*` - Result ranking and scoring
- `chaos.*` - Chaos engineering events
- `response.*` - Final response summary
- `ml.*` - ML prediction aggregates

This consistent naming makes it easy to:
- Autocomplete in SigNoz filters
- Understand attribute purpose at a glance
- Group related attributes visually
- Build reusable query templates

## Summary Statistics

**Total Span Attributes Added:**
- Root span: ~20 attributes
- Query parser: ~10 attributes
- Search index: ~15 attributes
- ML model: ~15 attributes
- Wikipedia API: ~20 attributes
- Ranker: ~20 attributes

**Total: ~100 comprehensive span attributes** across all components, providing deep visibility into every aspect of request processing!
