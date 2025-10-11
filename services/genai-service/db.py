# genai-service/db.py
"""
Simple DB helper using psycopg (v3) + SQL to fetch feedback rows.
Uses a connection pool for efficient, scalable connections.

This module expects the DATABASE_URL env var in standard PostgreSQL URI form:
  postgresql://user:password@host:port/dbname
"""

import os
import atexit
from psycopg import sql
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger("genai-service.db")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.warning("DATABASE_URL not set. DB operations will fail until it's configured.")

FEEDBACK_TABLE = os.getenv("FEEDBACK_TABLE", "feedback")
TIMESTAMP_COL = os.getenv("TIMESTAMP_COL", "created_at")

# --- FIX 1: Implement a Database Connection Pool ---
# This pool is created once when the application starts and reuses connections.
# It's much more efficient than creating a new connection for every request.
pool = None
if DATABASE_URL:
    # min_size=1 ensures at least one connection is ready.
    # max_size=10 limits the number of concurrent connections to the database.
    pool = ConnectionPool(conninfo=DATABASE_URL, min_size=1, max_size=10)
    # Ensure the pool is closed gracefully when the application shuts down.
    atexit.register(pool.close)

def get_feedbacks_for_date(target_date: date):
    """
    Return a list of rows (as dicts) for feedbacks where TIMESTAMP_COL is within target_date.
    """
    if not pool:
        raise RuntimeError("Database connection pool is not available. Check DATABASE_URL.")

    start = datetime.combine(target_date, datetime.min.time())
    end = start + timedelta(days=1)

    # A 'with' statement gets a connection from the pool and automatically returns it.
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # --- FIX 2: Prevent SQL Injection ---
            # Use sql.Identifier to safely quote the table and column names.
            # This is the correct way to prevent SQL injection with dynamic identifiers.
            query = sql.SQL("""
                SELECT *
                FROM {table}
                WHERE {timestamp_col} >= %s AND {timestamp_col} < %s
                ORDER BY {timestamp_col} ASC
            """).format(
                table=sql.Identifier(FEEDBACK_TABLE),
                timestamp_col=sql.Identifier(TIMESTAMP_COL)
            )
            cur.execute(query, (start, end))
            rows = cur.fetchall()
            return rows