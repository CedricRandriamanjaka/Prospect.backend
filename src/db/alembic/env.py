"""
Configuration Alembic simplifiée pour les migrations.
Utilise l'URL directe (sans pooler) pour les migrations, recommandée par Neon.
"""
import os
from logging.config import fileConfig
from sqlalchemy import pool, create_engine
from alembic import context
from pathlib import Path
from dotenv import load_dotenv

# Import de la base de données centralisée
import sys

# Ajouter le répertoire parent au path pour les imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Charger .env pour avoir accès aux variables d'environnement
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Imports depuis src/
from src.db.database import Base
# Importe tous les modèles pour qu'Alembic les détecte
from src.model.models import *

# Configuration Alembic
config = context.config

# Configurer le logging si un fichier de config existe
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Métadonnées pour Alembic (tous les modèles)
target_metadata = Base.metadata


def get_alembic_url() -> str:
    """
    Récupère l'URL pour Alembic.
    Priorité : DATABASE_URL_MIGRATIONS > DATABASE_URL (converti sans pooler)
    
    Pour les migrations, Neon recommande d'utiliser l'endpoint direct
    (sans -pooler) car plus stable pour les opérations DDL.
    """
    # Option 1 : URL dédiée aux migrations (endpoint direct)
    url = os.environ.get("DATABASE_URL_MIGRATIONS")
    
    if url:
        url = url.strip()
    else:
        # Option 2 : Convertir DATABASE_URL en endpoint direct (sans pooler)
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise ValueError(
                "DATABASE_URL ou DATABASE_URL_MIGRATIONS doit être défini dans .env"
            )
        url = url.strip()
        
        # Convertir -pooler vers endpoint direct
        # ep-xxx-pooler.region.aws.neon.tech -> ep-xxx.region.aws.neon.tech
        if "-pooler" in url:
            url = url.replace("-pooler", "", 1)
    
    # Convertir pour psycopg3 (driver moderne)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    return url


def run_migrations_offline() -> None:
    """Exécute les migrations en mode offline."""
    url = get_alembic_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécute les migrations en mode online avec l'URL directe."""
    # Créer un engine spécifique pour Alembic avec l'URL directe (sans pooler)
    alembic_url = get_alembic_url()
    
    connectable = create_engine(
        alembic_url,
        poolclass=pool.NullPool,
        connect_args={
            "connect_timeout": 60,  # 60 secondes pour Neon qui peut être en pause
        },
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    except Exception as e:
        error_msg = str(e).lower()
        if "timeout" in error_msg or "connection" in error_msg:
            print("\n" + "="*70)
            print("⚠️  ERREUR DE CONNEXION À LA BASE DE DONNÉES")
            print("="*70)
            print("\nImpossible de se connecter à Neon.")
            print("\n🔍 DIAGNOSTIC :")
            print("  - Port 5432 peut être bloqué par firewall/réseau")
            print("  - Base Neon peut être en pause (statut 'Idle')")
            print("\n💡 SOLUTIONS :")
            print("  1. Réveillez la base depuis le dashboard Neon")
            print("  2. Testez depuis un autre réseau (4G/5G)")
            print("  3. Vérifiez que le port sortant 5432 n'est pas bloqué")
            print("  4. Utilisez DATABASE_URL_MIGRATIONS (endpoint direct sans -pooler)")
            print("  5. Générez une migration MANUELLE sans connexion :")
            print("     python -m alembic revision -m 'description'")
            print("     (puis éditez le fichier généré manuellement)")
            print("\n📝 Note : Les migrations utilisent l'endpoint direct (sans pooler)")
            print("   pour plus de stabilité avec les opérations DDL.")
            print("="*70 + "\n")
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
