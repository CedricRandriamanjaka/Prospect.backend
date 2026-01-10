"""
Ce module est déprécié. Utilisez database.py et models.py à la racine de src/.
Conservé pour compatibilité ascendante.
"""
from ..database import (
    engine,
    SessionLocal,
    get_db as db_session,
    get_database_url as get_db_url,
)

__all__ = [
    "engine",
    "SessionLocal",
    "db_session",
    "get_db_url",
]
