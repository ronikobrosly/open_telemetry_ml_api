from opentelemetry import metrics

# Get meter
meter = metrics.get_meter(__name__)

# Counter metrics
http_requests_total = meter.create_counter(
    name="http.requests.total",
    description="Total HTTP requests",
    unit="1"
)

search_queries_total = meter.create_counter(
    name="search.queries.total",
    description="Total search queries",
    unit="1"
)

model_predictions_total = meter.create_counter(
    name="model.predictions.total",
    description="Total ML model predictions",
    unit="1"
)

external_api_calls_total = meter.create_counter(
    name="external.api.calls.total",
    description="Total external API calls",
    unit="1"
)

chaos_events_total = meter.create_counter(
    name="chaos.events.total",
    description="Total chaos events triggered",
    unit="1"
)

# Histogram metrics
http_request_duration = meter.create_histogram(
    name="http.request.duration",
    description="HTTP request duration",
    unit="ms"
)

component_duration = meter.create_histogram(
    name="component.duration",
    description="Component execution duration",
    unit="ms"
)

model_inference_duration = meter.create_histogram(
    name="model.inference.duration",
    description="ML model inference duration",
    unit="ms"
)

model_score_distribution = meter.create_histogram(
    name="model.score.distribution",
    description="ML model score distribution",
    unit="1"
)

# Helper functions
def record_http_request(method: str, route: str, status_code: int, duration_ms: float):
    """Record HTTP request metrics"""
    http_requests_total.add(1, {"method": method, "route": route, "status_code": str(status_code)})
    http_request_duration.record(duration_ms, {"method": method, "route": route})

def record_search_query(intent: str):
    """Record search query metrics"""
    search_queries_total.add(1, {"intent": intent})

def record_model_prediction(status: str, duration_ms: float, score: float = None):
    """Record ML model prediction metrics"""
    model_predictions_total.add(1, {"status": status})
    model_inference_duration.record(duration_ms)
    if score is not None:
        model_score_distribution.record(score)

def record_external_api_call(source: str, status: str):
    """Record external API call metrics"""
    external_api_calls_total.add(1, {"source": source, "status": status})

def record_chaos_event(event_type: str):
    """Record chaos event metrics"""
    chaos_events_total.add(1, {"event_type": event_type})

def record_component_duration(component: str, duration_ms: float):
    """Record component execution duration"""
    component_duration.record(duration_ms, {"component": component})
