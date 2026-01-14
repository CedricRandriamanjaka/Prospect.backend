# src/db/connection.py
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Iterable, Optional

from dotenv import load_dotenv

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from psycopg.types.json import Json

# Charger le fichier .env (même logique que ton ancien database.py)
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

def get_database_url() -> str:
    """
    Retourne DATABASE_URL au format psycopg (postgresql://...).
    Neon pooler OK ici (recommandé côté app).
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL n'est pas défini dans .env\n"
            "Format attendu: postgresql://user:password@host:port/database?sslmode=require"
        )
    return url.strip()

DATABASE_URL = get_database_url()

# Pool léger pour microservice
pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=5,
    kwargs={"connect_timeout": 60},  # Neon peut être en pause
)

@contextmanager
def get_conn():
    """
    Context manager de connexion (auto-commit géré par psycopg via transaction explicite).
    """
    with pool.connection() as conn:
        yield conn

def fetch_one(sql: str, params: Optional[Iterable[Any]] = None) -> Optional[dict]:
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()

def fetch_all(sql: str, params: Optional[Iterable[Any]] = None) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            return list(cur.fetchall())

def execute(sql: str, params: Optional[Iterable[Any]] = None) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()

def test_connection() -> bool:
    try:
        row = fetch_one("SELECT 1 AS ok;")
        return bool(row and row.get("ok") == 1)
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return False

__all__ = ["Json", "pool", "get_database_url", "get_conn", "fetch_one", "fetch_all", "execute", "test_connection"]
