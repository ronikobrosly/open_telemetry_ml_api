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
