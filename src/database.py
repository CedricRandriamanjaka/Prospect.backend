"""
Configuration centralisée de la base de données.
Approche simple et moderne, similaire à Prisma.
"""
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Charger le fichier .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Base pour tous les modèles ORM (comme Prisma)
Base = declarative_base()


def get_database_url() -> str:
    """Récupère et formate l'URL de la base de données pour psycopg3."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL n'est pas défini dans le fichier .env\n"
            "Format attendu: postgresql://user:password@host:port/database"
        )
    
    url = url.strip()
    # Convertir pour psycopg3 (driver moderne de PostgreSQL)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    return url


# Configuration de l'engine avec timeout augmenté pour Neon
# Neon peut être en pause et nécessiter quelques secondes pour se réveiller
DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Pas de pool pour Alembic/migrations
    connect_args={
        "connect_timeout": 60,  # 60 secondes pour Neon qui peut être en pause
    },
    echo=False,  # Mettre à True pour voir les requêtes SQL en debug
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency pour FastAPI: retourne une session DB.
    Usage:
        @app.get("/")
        def route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    """Teste la connexion à la base de données."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return False
