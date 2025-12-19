import random
import time
import math
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from app.core.metrics import record_chaos_event
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
        span = trace.get_current_span()
        inference_start = time.time()

        # Chaos injection: model failure
        if chaos_manager.should_trigger_model_failure():
            span.set_attribute("chaos.triggered", True)
            span.set_attribute("chaos.event_type", "model_failure")
            record_chaos_event("model_failure")
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

        # Record inference time in span
        actual_inference_time_ms = (time.time() - inference_start) * 1000
        span.set_attribute("model.inference_time_ms", actual_inference_time_ms)

        return ModelPrediction(
            score=score,
            confidence=confidence,
            model_version=self.version
        )
