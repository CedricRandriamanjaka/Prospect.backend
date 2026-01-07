"""Modèles SQLAlchemy pour la base de données."""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, BigInteger, Float, Text, DateTime, ForeignKey, func, UniqueConstraint, text as sql_text
from sqlalchemy.dialects.postgresql import JSONB, UUID


class Base(DeclarativeBase):
    pass


class CityBBox(Base):
    """Cache des bounding boxes des villes."""
    __tablename__ = "city_bbox"

    city_key: Mapped[str] = mapped_column(String, primary_key=True)
    south: Mapped[float] = mapped_column(Float, nullable=False)
    west: Mapped[float] = mapped_column(Float, nullable=False)
    north: Mapped[float] = mapped_column(Float, nullable=False)
    east: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Prospect(Base):
    """Prospects récupérés depuis OSM."""
    __tablename__ = "prospect"
    __table_args__ = (UniqueConstraint("osm_type", "osm_id", name="uq_osm"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=sql_text("gen_random_uuid()"))

    city_key: Mapped[str] = mapped_column(String, ForeignKey("city_bbox.city_key", ondelete="CASCADE"), nullable=False)

    osm_type: Mapped[str] = mapped_column(String, nullable=False)  # node/way/relation
    osm_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    name: Mapped[str | None] = mapped_column(Text)
    activity_type: Mapped[str | None] = mapped_column(String)
    activity_value: Mapped[str | None] = mapped_column(String)

    website: Mapped[str | None] = mapped_column(Text)
    emails: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sql_text("'[]'::jsonb"))
    phones: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sql_text("'[]'::jsonb"))

    stars: Mapped[str | None] = mapped_column(String)
    cuisine: Mapped[str | None] = mapped_column(String)
    opening_hours: Mapped[str | None] = mapped_column(Text)
    operator: Mapped[str | None] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(Text)

    address: Mapped[dict | None] = mapped_column(JSONB)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)

    osm_url: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String, nullable=False, server_default=sql_text("'OpenStreetMap'"))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SearchCache(Base):
    """Cache des résultats de recherche avec TTL."""
    __tablename__ = "search_cache"

    cache_key: Mapped[str] = mapped_column(String, primary_key=True)
    city_key: Mapped[str] = mapped_column(String, ForeignKey("city_bbox.city_key", ondelete="CASCADE"), nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    results: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
