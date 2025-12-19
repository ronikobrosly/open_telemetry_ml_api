import sqlite3
import json
import time
import random
from typing import List
from opentelemetry import trace
from app.core.metrics import record_chaos_event
from app.schemas.internal import SearchIndexResult, ParsedQuery
from app.core.config import settings
from app.core.chaos import chaos_manager

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

        # Chaos injection: slow search
        if chaos_manager.should_trigger_slow_search():
            span.set_attribute("chaos.triggered", True)
            span.set_attribute("chaos.event_type", "slow_search")
            record_chaos_event("slow_search")
            time.sleep(settings.search_slow_threshold_ms / 1000.0)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build FTS query: OR all tokens together
        fts_query = ' OR '.join(parsed_query.tokens)

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
        return results[:limit]
