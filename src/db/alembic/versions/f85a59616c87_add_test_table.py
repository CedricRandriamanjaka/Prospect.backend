"""add test table

Revision ID: f85a59616c87
Revises: 
Create Date: 2026-01-10 15:04:10.956919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f85a59616c87'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Créer l'extension pgcrypto pour gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    
    # Créer la table test_table
    op.create_table(
        'test_table',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Supprimer la table test_table
    op.drop_table('test_table')
    # Note: On ne supprime pas l'extension pgcrypto car elle peut être utilisée ailleurs
