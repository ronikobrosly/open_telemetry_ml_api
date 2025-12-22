import sqlite3
import json
import time
import random
import logging
from typing import List
from opentelemetry import trace
from app.core.metrics import record_chaos_event
from app.schemas.internal import SearchIndexResult, ParsedQuery
from app.core.config import settings
from app.core.chaos import chaos_manager

logger = logging.getLogger(__name__)

class SearchIndex:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def search(self, parsed_query: ParsedQuery, limit: int = 10) -> List[SearchIndexResult]:
        """
        Search documents using SQLite FTS5

        Algorithm:
        1. Check chaos config for slow search injection
        2. Build FTS query from parsed tokens
        3. Execute FTS search
        4. Calculate base_score using BM25 rank (normalized)
        5. Count matching tokens for each result
        """
        span = trace.get_current_span()

        # Add search parameters to span
        span.set_attribute("search.limit", limit)
        span.set_attribute("search.query_tokens", ",".join(parsed_query.tokens))
        span.set_attribute("search.token_count", parsed_query.token_count)
        span.set_attribute("search.query_intent", parsed_query.intent.value)

        # Chaos injection: slow search
        if chaos_manager.should_trigger_slow_search():
            span.set_attribute("chaos.triggered", True)
            span.set_attribute("chaos.event_type", "slow_search")
            record_chaos_event("slow_search")
            logger.warning("Chaos: slow search", extra={
                "delay_ms": settings.search_slow_threshold_ms
            })
            time.sleep(settings.search_slow_threshold_ms / 1000.0)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build FTS query: OR all tokens together
        fts_query = ' OR '.join(parsed_query.tokens)
        span.set_attribute("search.fts_query", fts_query)

        # Execute FTS search
        cursor.execute("""
            SELECT
                d.doc_id,
                d.title,
                d.text,
                fts.rank as bm25_rank
            FROM documents_fts fts
            JOIN documents d ON d.rowid = fts.rowid
            WHERE documents_fts MATCH ?
            ORDER BY fts.rank
            LIMIT ?
        """, (fts_query, limit * 2))  # Fetch extra for diversity

        results = []
        for row in cursor.fetchall():
            # Calculate match count
            text_lower = (row['title'] + ' ' + row['text']).lower()
            match_count = sum(1 for token in parsed_query.tokens if token in text_lower)

            # Normalize BM25 rank to [0, 1] using sigmoid
            # BM25 rank is negative; closer to 0 is better
            base_score = 1.0 / (1.0 + abs(row['bm25_rank']))

            results.append(SearchIndexResult(
                doc_id=row['doc_id'],
                title=row['title'],
                text=row['text'][:200],  # Truncate to snippet
                base_score=base_score,
                match_count=match_count
            ))

        conn.close()

        # Limit to requested amount
        final_results = results[:limit]

        # Add result attributes to span
        span.set_attribute("search.results_found", len(final_results))
        span.set_attribute("search.results_before_limit", len(results))

        if final_results:
            avg_score = sum(r.base_score for r in final_results) / len(final_results)
            span.set_attribute("search.avg_base_score", round(avg_score, 3))
            span.set_attribute("search.max_base_score", round(max(r.base_score for r in final_results), 3))
            span.set_attribute("search.min_base_score", round(min(r.base_score for r in final_results), 3))
            span.set_attribute("search.top_doc_id", final_results[0].doc_id)
            span.set_attribute("search.top_doc_title", final_results[0].title)
            span.set_attribute("search.top_doc_ids", ",".join([r.doc_id for r in final_results[:3]]))

        return final_results
