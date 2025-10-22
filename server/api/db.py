import os
import psycopg2
from psycopg2 import OperationalError

_conn = None

def init_db(db_url):
    global _conn
    if not db_url:
        print("[db] No DATABASE_URL provided, skipping DB init.")
        return
    try:
        _conn = psycopg2.connect(db_url)
        with _conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id SERIAL PRIMARY KEY,
                prompt TEXT,
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            _conn.commit()
        print("[db] Connected and ensured tables exist.")
    except OperationalError as e:
        _conn = None
        print(f"[db] Could not connect to database: {e}. Continuing without DB (dev mode).")

def get_session():
    class Sess:
        def insert_query(self, prompt, response):
            if not _conn:
                print("[db] DB not connected — skipping insert.")
                return
            with _conn.cursor() as cur:
                cur.execute("INSERT INTO queries (prompt, response) VALUES (%s, %s)", (prompt, response))
                _conn.commit()
    return Sess()
