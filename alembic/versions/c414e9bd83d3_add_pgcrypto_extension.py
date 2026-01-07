"""add_pgcrypto_extension

Revision ID: c414e9bd83d3
Revises: 7937f50ca760
Create Date: 2026-01-07 14:55:56.466736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c414e9bd83d3'
down_revision: Union[str, None] = '7937f50ca760'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Créer l'extension pgcrypto pour gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")


def downgrade() -> None:
    # Supprimer l'extension (optionnel, généralement on ne la supprime pas)
    # op.execute("DROP EXTENSION IF EXISTS pgcrypto;")
    pass
