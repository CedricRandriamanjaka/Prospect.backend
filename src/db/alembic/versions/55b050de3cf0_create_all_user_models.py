"""create_all_user_models

Revision ID: 55b050de3cf0
Revises: 4b45faa94786
Create Date: 2026-01-10 21:43:00.305506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '55b050de3cf0'
down_revision: Union[str, None] = '4b45faa94786'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Créer l'extension pgcrypto pour gen_random_uuid() si pas déjà fait
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    
    # ========================================================================
    # 1. ROLES (pas de dépendance)
    # ========================================================================
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_roles_name', 'roles', ['name'])
    
    # ========================================================================
    # 2. USERS (dépend de roles)
    # ========================================================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('password', sa.String(), nullable=True),
        sa.Column('auth_provider', sa.String(), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_role_id', 'users', ['role_id'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    
    # ========================================================================
    # 3. COMPANIES (pas de dépendance)
    # ========================================================================
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('siret', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('siret')
    )
    op.create_index('ix_companies_name', 'companies', ['name'])
    op.create_index('ix_companies_siret', 'companies', ['siret'])
    op.create_index('ix_companies_city', 'companies', ['city'])
    
    # ========================================================================
    # 4. PROFILES (dépend de users et companies)
    # ========================================================================
    op.create_table(
        'profiles',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('firstname', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=False, server_default=sa.text("'fr'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_profiles_user_id', 'profiles', ['user_id'])
    op.create_index('ix_profiles_email', 'profiles', ['email'])
    op.create_index('ix_profiles_city', 'profiles', ['city'])
    op.create_index('ix_profiles_company_id', 'profiles', ['company_id'])
    
    # ========================================================================
    # 5. PRICING_PLANS (pas de dépendance)
    # ========================================================================
    op.create_table(
        'pricing_plans',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.NUMERIC(10, 2), nullable=False),
        sa.Column('currency', sa.String(), nullable=False, server_default=sa.text("'EUR'")),
        sa.Column('price_promo', sa.NUMERIC(10, 2), nullable=True),
        sa.Column('price_promo_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('price_promo_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billing_period', sa.String(), nullable=False),
        sa.Column('max_prospects', sa.Integer(), nullable=True),
        sa.Column('max_prospects_per_hour', sa.Integer(), nullable=True),
        sa.Column('max_prospects_per_day', sa.Integer(), nullable=True),
        sa.Column('count_limit', sa.Integer(), nullable=True),
        sa.Column('geoloc_limit', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_display', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('price >= 0', name='check_price_positive'),
        sa.CheckConstraint(
            "(price_promo_start_date IS NULL AND price_promo_end_date IS NULL) OR "
            "(price_promo_start_date IS NOT NULL AND price_promo_end_date IS NOT NULL AND "
            "price_promo_end_date > price_promo_start_date)",
            name='check_promo_dates'
        ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pricing_plans_is_active', 'pricing_plans', ['is_active'])
    op.create_index('idx_pricing_plans_billing_period', 'pricing_plans', ['billing_period'])
    
    # ========================================================================
    # 6. ABONNEMENTS (dépend de users et pricing_plans)
    # ========================================================================
    op.create_table(
        'abonnements',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('pricing_plan_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.String(), nullable=True),
        sa.Column('payment_status', sa.String(), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('end_date > start_date', name='check_end_after_start'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pricing_plan_id'], ['pricing_plans.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_abonnements_user_id', 'abonnements', ['user_id'])
    op.create_index('ix_abonnements_pricing_plan_id', 'abonnements', ['pricing_plan_id'])
    op.create_index('ix_abonnements_is_active', 'abonnements', ['is_active'])
    op.create_index('ix_abonnements_end_date', 'abonnements', ['end_date'])
    op.create_index('idx_abonnements_user_active', 'abonnements', ['user_id', 'is_active'])
    
    # ========================================================================
    # 7. SEARCH_TYPES (pas de dépendance)
    # ========================================================================
    op.create_table(
        'search_types',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_search_types_name', 'search_types', ['name'])
    op.create_index('ix_search_types_is_active', 'search_types', ['is_active'])
    
    # ========================================================================
    # 8. SEARCH_HISTORY (dépend de users et search_types)
    # ========================================================================
    op.create_table(
        'search_history',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('search_type_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('search_query', sa.String(), nullable=False),
        sa.Column('results_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('filters_applied', postgresql.JSONB(), nullable=True),
        sa.Column('location', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['search_type_id'], ['search_types.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_search_history_user_id', 'search_history', ['user_id'])
    op.create_index('ix_search_history_created_at', 'search_history', ['created_at'])
    op.create_index('ix_search_history_search_type_id', 'search_history', ['search_type_id'])
    op.create_index('idx_search_history_user_created', 'search_history', ['user_id', 'created_at'])
    
    # ========================================================================
    # 9. SEARCH_RESULTS (dépend de search_history)
    # ========================================================================
    op.create_table(
        'search_results',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('search_history_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('result_type', sa.String(), nullable=True),
        sa.Column('result_data', postgresql.JSONB(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['search_history_id'], ['search_history.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_search_results_search_history_id', 'search_results', ['search_history_id'])
    op.create_index('ix_search_results_created_at', 'search_results', ['created_at'])
    op.create_index('ix_search_results_result_type', 'search_results', ['result_type'])
    
    # ========================================================================
    # 10. BLACK_LIST (dépend de users)
    # ========================================================================
    op.create_table(
        'black_list',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('date_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_black_list_email', 'black_list', ['email'])
    op.create_index('ix_black_list_user_id', 'black_list', ['user_id'])
    op.create_index('ix_black_list_is_active', 'black_list', ['is_active'])
    op.create_index('ix_black_list_date_end', 'black_list', ['date_end'])
    
    # ========================================================================
    # 11. API_KEYS (dépend de users)
    # ========================================================================
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'])
    op.create_index('ix_api_keys_expires_at', 'api_keys', ['expires_at'])


def downgrade() -> None:
    # Supprimer les tables dans l'ordre inverse des dépendances
    op.drop_table('api_keys')
    op.drop_table('black_list')
    op.drop_table('search_results')
    op.drop_table('search_history')
    op.drop_table('search_types')
    op.drop_table('abonnements')
    op.drop_table('pricing_plans')
    op.drop_table('profiles')
    op.drop_table('companies')
    op.drop_table('users')
    op.drop_table('roles')
