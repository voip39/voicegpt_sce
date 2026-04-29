from __future__ import annotations

import os
from typing import Any, Optional, Tuple, List

DB_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("PGURL")
    or os.getenv("DATABASE_URL_READWRITE")
)

if not DB_URL:
    raise RuntimeError("DATABASE_URL is required")

try:
    import psycopg2
    import psycopg2.extras
    _PG = "psycopg2"
except ImportError:
    import psycopg
    _PG = "psycopg"


def get_conn():
    if _PG == "psycopg2":
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        return conn

    conn = psycopg.connect(DB_URL)
    try:
        conn.autocommit = True
    except Exception:
        pass
    return conn


def _row_to_dict(cur, row):
    if row is None:
        return None
    columns = [desc[0] for desc in cur.description]
    return dict(zip(columns, row))


def db_one(sql: str, params: Tuple[Any, ...] | None = None) -> Optional[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            row = cur.fetchone()
            return _row_to_dict(cur, row)


def db_all(sql: str, params: Tuple[Any, ...] | None = None) -> List[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            return [_row_to_dict(cur, r) for r in rows or []]


def db_exec(sql: str, params: Tuple[Any, ...] | None = None) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            try:
                return cur.rowcount
            except Exception:
                return 0