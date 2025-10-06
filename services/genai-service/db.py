# genai-service/db.py
"""
Simple DB helper using psycopg2 + SQL to fetch feedback rows.

This module expects the DATABASE_URL env var in standard PostgreSQL URI form:
  postgresql://user:password@host:port/dbname

Configurable environment variables:
 - DATABASE_URL
 - FEEDBACK_TABLE (default: feedback)
 - TIMESTAMP_COL (default: created_at)
 - TEXT_COL (optional, default tries several)
"""


import os
import psycopg
from psycopg.rows import dict_row # <-- Import the row factory
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger("genai-service.db")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.warning("DATABASE_URL not set. DB operations will fail until it's configured.")

FEEDBACK_TABLE = os.getenv("FEEDBACK_TABLE", "feedback")
TIMESTAMP_COL = os.getenv("TIMESTAMP_COL", "created_at")
TEXT_COL = os.getenv("TEXT_COL", "")  # optional, if empty we will try common names

# A helper for safe queries
def _connect():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not configured")
    conn = psycopg.connect(DATABASE_URL)
    return conn

def get_feedbacks_for_date(target_date: date):
    """
    Return a list of rows (as dicts) for feedbacks where TIMESTAMP_COL is within target_date (local date).
    Uses inclusive start (00:00:00) to exclusive next day start.
    """
    start = datetime.combine(target_date, datetime.min.time())
    end = start + timedelta(days=1)
    conn = _connect()
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            text_col_fragment = _determine_text_column(cur)
            sql = f"""
                SELECT *
                FROM {FEEDBACK_TABLE}
                WHERE {TIMESTAMP_COL} >= %s AND {TIMESTAMP_COL} < %s
                ORDER BY {TIMESTAMP_COL} ASC
            """
            # Because psycopg2.sql.Identifier.string is not safe here; to keep it simple and avoid
            # introducing sql module complexity, we'll format table/col names with validation.
            # Validate table and column names (only allow alphanumerics and underscore)
            if not _is_safe_identifier(FEEDBACK_TABLE) or not _is_safe_identifier(TIMESTAMP_COL):
                raise ValueError("FEEDBACK_TABLE or TIMESTAMP_COL contains unsafe characters")

            sql = f"""
                SELECT *
                FROM {FEEDBACK_TABLE}
                WHERE {TIMESTAMP_COL} >= %s AND {TIMESTAMP_COL} < %s
                ORDER BY {TIMESTAMP_COL} ASC
            """
            cur.execute(sql, (start, end))
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()

def _determine_text_column(cur):
    """
    Try to pick a text column automatically; not used in current implementation,
    kept for future improvements.
    """
    if TEXT_COL and _is_safe_identifier(TEXT_COL):
        return TEXT_COL
    # otherwise we'll discover columns
    return None

def _is_safe_identifier(name: str) -> bool:
    # allow only letters, digits, underscore, optionally dot
    import re
    return bool(re.match(r'^[A-Za-z0-9_]+$', name))
