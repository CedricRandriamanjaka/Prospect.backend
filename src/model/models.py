"""
Modèles ORM pour l'application Prospect.
"""
from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Float, 
    Text, text, Index, ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
from sqlalchemy.orm import relationship

from ..db.database import Base


class TestTable(Base):
    """
    Table de test simple.
    """
    __tablename__ = "test_table"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    name = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False
    )


class OpenStreetMapEnrichi(Base):
    """
    Table pour enregistrer les données d'enrichissement des sites web.
    Cache les résultats de scraping pour éviter de re-scraper les mêmes sites.
    """
    __tablename__ = "openstreetmap_enrichi"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    website = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )
    emails = Column(JSONB, nullable=True)
    telephones = Column(JSONB, nullable=True)
    whatsapp = Column(JSONB, nullable=True)
    scraped_urls = Column(JSONB, nullable=True)
    is_empty = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    __table_args__ = (
        Index('idx_openstreetmap_enrichi_website', 'website'),
        Index('idx_openstreetmap_enrichi_updated_at', 'updated_at'),
    )


# =============================================================================
# MODÈLES PRINCIPAUX - AUTHENTIFICATION ET UTILISATEURS
# =============================================================================

class Role(Base):
    """Table des rôles utilisateurs."""
    __tablename__ = "roles"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    name = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    # Relations
    users = relationship("User", back_populates="role")


class User(Base):
    """Table des utilisateurs."""
    __tablename__ = "users"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    role_id = Column(
        UUID(as_uuid=False),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=True)
    password = Column(String, nullable=True)
    auth_provider = Column(String, nullable=True)  # 'google', 'github', 'email', etc.
    email_verified = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"), index=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    # Relations
    role = relationship("Role", back_populates="users")
    profile = relationship("Profile", back_populates="user", uselist=False)
    abonnements = relationship("Abonnement", back_populates="user")
    search_histories = relationship("SearchHistory", back_populates="user")
    black_lists = relationship("BlackList", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")


class Profile(Base):
    """Table des profils utilisateurs."""
    __tablename__ = "profiles"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    name = Column(String, nullable=True)
    firstname = Column(String, nullable=True)
    city = Column(String, nullable=True, index=True)
    country = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True, index=True)
    website = Column(String, nullable=True)
    company_id = Column(
        UUID(as_uuid=False),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    avatar_url = Column(String, nullable=True)
    language = Column(String, nullable=False, default="fr", server_default=text("'fr'"))
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    # Relations
    user = relationship("User", back_populates="profile")
    company = relationship("Company", back_populates="profiles")


class Company(Base):
    """Table des entreprises."""
    __tablename__ = "companies"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    name = Column(String, nullable=False, index=True)
    siret = Column(String, nullable=True, unique=True, index=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True, index=True)
    country = Column(String, nullable=True)
    website = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    # Relations
    profiles = relationship("Profile", back_populates="company")


# =============================================================================
# MODÈLES - ABONNEMENTS ET TARIFICATION
# =============================================================================

class PricingPlan(Base):
    """Table des plans de tarification."""
    __tablename__ = "pricing_plans"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(NUMERIC(10, 2), nullable=False)
    currency = Column(String, nullable=False, default="EUR", server_default=text("'EUR'"))
    price_promo = Column(NUMERIC(10, 2), nullable=True)
    price_promo_start_date = Column(DateTime(timezone=True), nullable=True)
    price_promo_end_date = Column(DateTime(timezone=True), nullable=True)
    billing_period = Column(String, nullable=False, index=True)  # 'monthly', 'yearly', 'lifetime'
    max_prospects = Column(Integer, nullable=True)  # null = illimité
    max_prospects_per_hour = Column(Integer, nullable=True)
    max_prospects_per_day = Column(Integer, nullable=True)
    count_limit = Column(Integer, nullable=True)
    geoloc_limit = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"), index=True)
    is_display = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    # Relations
    abonnements = relationship("Abonnement", back_populates="pricing_plan")
    
    __table_args__ = (
        CheckConstraint('price >= 0', name='check_price_positive'),
        CheckConstraint(
            '(price_promo_start_date IS NULL AND price_promo_end_date IS NULL) OR '
            '(price_promo_start_date IS NOT NULL AND price_promo_end_date IS NOT NULL AND '
            'price_promo_end_date > price_promo_start_date)',
            name='check_promo_dates'
        ),
        Index('idx_pricing_plans_is_active', 'is_active'),
        Index('idx_pricing_plans_billing_period', 'billing_period'),
    )


class Abonnement(Base):
    """Table des abonnements utilisateurs."""
    __tablename__ = "abonnements"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    pricing_plan_id = Column(
        UUID(as_uuid=False),
        ForeignKey("pricing_plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False, index=True)
    auto_renew = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(String, nullable=True)
    payment_status = Column(String, nullable=False, default="pending", server_default=text("'pending'"))  # 'pending', 'paid', 'failed', 'refunded'
    stripe_subscription_id = Column(String, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"), index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    # Relations
    user = relationship("User", back_populates="abonnements")
    pricing_plan = relationship("PricingPlan", back_populates="abonnements")
    
    __table_args__ = (
        CheckConstraint('end_date > start_date', name='check_end_after_start'),
        Index('idx_abonnements_user_active', 'user_id', 'is_active'),
    )


# =============================================================================
# MODÈLES - RECHERCHE
# =============================================================================

class SearchType(Base):
    """Table des types de recherche."""
    __tablename__ = "search_types"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    name = Column(String, nullable=False, unique=True, index=True)  # 'osm', 'linkedin', 'facebook', etc.
    description = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"), index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    # Relations
    search_histories = relationship("SearchHistory", back_populates="search_type")


class SearchHistory(Base):
    """Table de l'historique des recherches."""
    __tablename__ = "search_history"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    search_type_id = Column(
        UUID(as_uuid=False),
        ForeignKey("search_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    search_query = Column(String, nullable=False)
    results_count = Column(Integer, nullable=False, default=0, server_default=text("0"))
    execution_time_ms = Column(Integer, nullable=True)
    filters_applied = Column(JSONB, nullable=True)  # filtres utilisés en JSON
    location = Column(JSONB, nullable=True)  # {lat, lon, radius} si recherche géolocalisée
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    # Relations
    user = relationship("User", back_populates="search_histories")
    search_type = relationship("SearchType", back_populates="search_histories")
    search_results = relationship("SearchResult", back_populates="search_history", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_search_history_user_created', 'user_id', 'created_at'),
    )


class SearchResult(Base):
    """Table des résultats de recherche."""
    __tablename__ = "search_results"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    search_history_id = Column(
        UUID(as_uuid=False),
        ForeignKey("search_history.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    result_type = Column(String, nullable=True, index=True)  # 'prospect', 'company', etc.
    result_data = Column(JSONB, nullable=False)  # données complètes du résultat
    score = Column(Float, nullable=True)  # score de pertinence
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    # Relations
    search_history = relationship("SearchHistory", back_populates="search_results")


# =============================================================================
# MODÈLES - AUTRES
# =============================================================================

class BlackList(Base):
    """Table de la liste noire (emails bloqués)."""
    __tablename__ = "black_list"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    email = Column(String, nullable=False, unique=True, index=True)
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )  # null = globale, sinon spécifique à l'utilisateur
    reason = Column(String, nullable=True)  # raison du blocage
    date_end = Column(DateTime(timezone=True), nullable=True, index=True)  # null = permanent
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"), index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    # Relations
    user = relationship("User", back_populates="black_lists")


class ApiKey(Base):
    """Table des clés API utilisateurs."""
    __tablename__ = "api_keys"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    key_hash = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)  # nom donné par l'utilisateur
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)  # null = jamais
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"), index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False
    )
    
    # Relations
    user = relationship("User", back_populates="api_keys")
