"""add_is_empty_column_to_openstreetmap_enrichi

Revision ID: 4b45faa94786
Revises: ccca7f629f40
Create Date: 2026-01-10 18:14:54.649192

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b45faa94786'
down_revision: Union[str, None] = 'ccca7f629f40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajouter la colonne is_empty avec valeur par défaut false
    op.add_column(
        'openstreetmap_enrichi',
        sa.Column('is_empty', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )
    
    # Mettre à jour les enregistrements existants pour calculer is_empty
    # Si emails, telephones et whatsapp sont tous vides, alors is_empty = true
    op.execute("""
        UPDATE openstreetmap_enrichi
        SET is_empty = CASE
            WHEN (emails IS NULL OR jsonb_array_length(emails) = 0)
                 AND (telephones IS NULL OR jsonb_array_length(telephones) = 0)
                 AND (whatsapp IS NULL OR jsonb_array_length(whatsapp) = 0)
            THEN true
            ELSE false
        END
    """)


def downgrade() -> None:
    # Supprimer la colonne is_empty
    op.drop_column('openstreetmap_enrichi', 'is_empty')
