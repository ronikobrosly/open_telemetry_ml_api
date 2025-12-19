import httpx
import asyncio
import logging
from typing import Optional
from opentelemetry import trace
from app.core.metrics import record_chaos_event
from app.schemas.internal import ExternalSignal, ParsedQuery
from app.core.config import settings
from app.core.chaos import chaos_manager

logger = logging.getLogger(__name__)

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
        span = trace.get_current_span()

        # Chaos injection: external API failure
        if chaos_manager.should_trigger_external_failure():
            span.set_attribute("chaos.triggered", True)
            span.set_attribute("chaos.event_type", "external_failure")
            record_chaos_event("external_failure")
            raise httpx.HTTPError("Simulated external API failure")

        # Chaos injection: timeout
        if chaos_manager.should_trigger_external_timeout():
            span.set_attribute("chaos.triggered", True)
            span.set_attribute("chaos.event_type", "external_timeout")
            record_chaos_event("external_timeout")
            await asyncio.sleep(settings.wikipedia_timeout + 1)
            raise httpx.TimeoutException("Simulated timeout")

        # Extract topic (use first meaningful token)
        topic = parsed_query.tokens[0] if parsed_query.tokens else "search"
        span.set_attribute("external.topic", topic)

        url = f"{self.base_url}/page/summary/{topic}"

        try:
            headers = {
                "User-Agent": "SearchRecommendationService/1.0 (OpenTelemetry Demo; +https://github.com/yourusername/project)"
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=self.timeout, headers=headers)

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

                    span.set_attribute("external.status", "success")
                    span.set_attribute("external.relevance_score", relevance_score)

                    return ExternalSignal(
                        source="wikipedia",
                        relevance_score=relevance_score,
                        description_length=description_length,
                        popularity_proxy=popularity_proxy
                    )
                else:
                    return None

        except (httpx.TimeoutException, httpx.HTTPError) as e:
            logger.warning("Wikipedia API error", extra={
                "topic": topic,
                "error": str(e),
                "error_type": type(e).__name__
            })
            return None
