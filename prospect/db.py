"""Configuration de la base de données SQLAlchemy."""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Charger le fichier .env depuis le répertoire courant
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def get_db_url() -> str:
    """Récupère et convertit l'URL de la base de données pour psycopg3."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL n'est pas défini. "
            "Créez un fichier .env dans Prospect.backend/ avec :\n"
            "DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require"
        )
    url = url.strip()
    # SQLAlchemy + psycopg3
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_engine(
    get_db_url(),
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=0,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def db_session():
    """Dependency pour FastAPI: retourne une session DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

