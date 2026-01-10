"""
Modèles ORM simplifiés - Table de test uniquement.
"""
from sqlalchemy import Column, String, DateTime, text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .database import Base


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
