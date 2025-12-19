import sqlite3
import os
from pathlib import Path
from .seed_data import generate_seed_documents

DATABASE_PATH = Path(__file__).parent / "search.db"

def init_database():
    """Initialize database with schema and seed data"""
    # Remove existing database for clean slate
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Read and execute schema
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)

    # Insert seed data
    documents = generate_seed_documents()
    for doc in documents:
        cursor.execute(
            "INSERT INTO documents (doc_id, title, text, category, embedding) VALUES (?, ?, ?, ?, ?)",
            (doc["doc_id"], doc["title"], doc["text"], doc["category"], doc["embedding"])
        )

    conn.commit()
    conn.close()

    return DATABASE_PATH

if __name__ == "__main__":
    db_path = init_database()
    print(f"Database initialized at: {db_path}")
