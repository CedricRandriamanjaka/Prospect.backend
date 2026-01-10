"""add_openstreetmap_enrichi_table

Revision ID: ccca7f629f40
Revises: f3e6a7d902ee
Create Date: 2026-01-10 17:55:54.661350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ccca7f629f40'
down_revision: Union[str, None] = 'f3e6a7d902ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Créer la table openstreetmap_enrichi
    op.create_table(
        'openstreetmap_enrichi',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('website', sa.String(), nullable=False),
        sa.Column('emails', postgresql.JSONB(), nullable=True),
        sa.Column('telephones', postgresql.JSONB(), nullable=True),
        sa.Column('whatsapp', postgresql.JSONB(), nullable=True),
        sa.Column('scraped_urls', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('website')
    )
    
    # Créer les index
    op.create_index('idx_openstreetmap_enrichi_website', 'openstreetmap_enrichi', ['website'])
    op.create_index('idx_openstreetmap_enrichi_updated_at', 'openstreetmap_enrichi', ['updated_at'])


def downgrade() -> None:
    # Supprimer les index
    op.drop_index('idx_openstreetmap_enrichi_updated_at', table_name='openstreetmap_enrichi')
    op.drop_index('idx_openstreetmap_enrichi_website', table_name='openstreetmap_enrichi')
    
    # Supprimer la table
    op.drop_table('openstreetmap_enrichi')
