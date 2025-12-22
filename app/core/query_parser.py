import re
from typing import List
from opentelemetry import trace
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
        span = trace.get_current_span()

        # Add initial query attributes
        span.set_attribute("query.original", query)
        span.set_attribute("query.length", len(query))

        # Normalize
        normalized = query.lower().strip()
        span.set_attribute("query.normalized", normalized)

        # Tokenize: split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', normalized)
        span.set_attribute("query.raw_token_count", len(tokens))

        # Remove stopwords
        filtered_tokens = [t for t in tokens if t not in self.stopwords and len(t) > 1]
        stopwords_removed = len(tokens) - len(filtered_tokens)
        span.set_attribute("query.stopwords_removed", stopwords_removed)

        # If no tokens remain after filtering, keep original tokens
        if not filtered_tokens:
            filtered_tokens = tokens
            span.set_attribute("query.fallback_to_raw_tokens", True)
        else:
            span.set_attribute("query.fallback_to_raw_tokens", False)

        # Detect intent
        intent = QueryIntent.DISCOVERY if len(filtered_tokens) <= 2 else QueryIntent.SEARCH

        # Add final attributes
        span.set_attribute("query.final_token_count", len(filtered_tokens))
        span.set_attribute("query.tokens", ",".join(filtered_tokens))
        span.set_attribute("query.intent", intent.value)

        return ParsedQuery(
            original=query,
            normalized=normalized,
            tokens=filtered_tokens,
            intent=intent,
            token_count=len(filtered_tokens)
        )
