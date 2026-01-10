"""
Configuration Alembic simplifiée pour les migrations.
"""
from logging.config import fileConfig
from sqlalchemy import pool
from alembic import context

# Import de la base de données centralisée
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Imports depuis src/
from src.database import Base, engine
# Importe tous les modèles pour qu'Alembic les détecte
from src.models import *

# Configuration Alembic
config = context.config

# Configurer le logging si un fichier de config existe
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Métadonnées pour Alembic (tous les modèles)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Exécute les migrations en mode offline."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécute les migrations en mode online."""
    # Utiliser l'engine directement depuis database.py
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
