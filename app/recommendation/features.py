import json
import sqlite3
from typing import List
from app.schemas.internal import ParsedQuery, SearchIndexResult, FeatureVector
from app.core.config import settings

CATEGORY_ENCODING = {
    "machine_learning": 0,
    "data_science": 1,
    "web_development": 2,
    "cloud_computing": 3,
    "cybersecurity": 4
}

class FeatureBuilder:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def build_features(
        self,
        parsed_query: ParsedQuery,
        doc: SearchIndexResult,
        user_id: str
    ) -> FeatureVector:
        """
        Build feature vector for ML model

        Features:
        - query_length: character count of original query
        - query_token_count: number of tokens
        - user_id_hash: stable hash of user_id (mod 1000)
        - doc_length: character count of document text
        - doc_category_encoded: integer encoding of category
        - query_doc_overlap: Jaccard similarity of query tokens and doc tokens
        - embedding_dot_product: dot product of query and doc embeddings
        """
        # Query features
        query_length = len(parsed_query.original)
        query_token_count = parsed_query.token_count

        # User feature
        user_id_hash = hash(user_id) % 1000

        # Document features
        doc_length = len(doc.text)

        # Get document category and embedding from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT category, embedding FROM documents WHERE doc_id = ?",
            (doc.doc_id,)
        )
        row = cursor.fetchone()
        conn.close()

        category = row[0] if row else "machine_learning"
        doc_embedding = json.loads(row[1]) if row else [0.0] * 8
        doc_category_encoded = CATEGORY_ENCODING.get(category, 0)

        # Query-doc overlap (Jaccard similarity)
        doc_tokens = set(doc.text.lower().split())
        query_tokens = set(parsed_query.tokens)
        intersection = len(query_tokens & doc_tokens)
        union = len(query_tokens | doc_tokens)
        query_doc_overlap = intersection / union if union > 0 else 0.0

        # Embedding similarity (generate query embedding on-the-fly)
        query_embedding = self._generate_query_embedding(parsed_query)
        embedding_dot_product = sum(
            q * d for q, d in zip(query_embedding, doc_embedding)
        )

        return FeatureVector(
            query_length=query_length,
            query_token_count=query_token_count,
            user_id_hash=user_id_hash,
            doc_length=doc_length,
            doc_category_encoded=doc_category_encoded,
            query_doc_overlap=query_doc_overlap,
            embedding_dot_product=embedding_dot_product
        )

    def _generate_query_embedding(self, parsed_query: ParsedQuery) -> List[float]:
        """
        Generate deterministic 8-dim embedding for query
        Uses hash of each token, combines with weighted average
        """
        if not parsed_query.tokens:
            return [0.0] * 8

        embeddings = []
        for token in parsed_query.tokens:
            token_hash = hash(token)
            embedding = [
                ((token_hash >> (i * 8)) & 0xFF) / 255.0 * 2 - 1
                for i in range(8)
            ]
            embeddings.append(embedding)

        # Average pooling
        avg_embedding = [
            sum(emb[i] for emb in embeddings) / len(embeddings)
            for i in range(8)
        ]

        return avg_embedding
