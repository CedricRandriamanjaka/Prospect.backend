"""Fonctions CRUD pour la base de données."""
from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.model.models import CityBBox, Prospect, SearchCache


def get_or_create_bbox(db: Session, city: str, bbox: Tuple[float, float, float, float]) -> CityBBox:
    """Récupère ou crée une entrée CityBBox pour une ville.
    
    Args:
        db: Session de base de données
        city: Nom de la ville (sera normalisé en city_key)
        bbox: Tuple (south, west, north, east)
    
    Returns:
        CityBBox existant ou nouvellement créé
    """
    city_key = city.strip().lower()
    south, west, north, east = bbox
    
    # Chercher l'existant
    stmt = select(CityBBox).where(CityBBox.city_key == city_key)
    existing = db.scalar(stmt)
    
    if existing:
        # Mettre à jour si les coordonnées ont changé
        if (existing.south != south or existing.west != west or 
            existing.north != north or existing.east != east):
            existing.south = south
            existing.west = west
            existing.north = north
            existing.east = east
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
        return existing
    
    # Créer nouveau
    new_bbox = CityBBox(
        city_key=city_key,
        south=south,
        west=west,
        north=north,
        east=east,
    )
    db.add(new_bbox)
    db.commit()
    db.refresh(new_bbox)
    return new_bbox


def get_cache(db: Session, city: str, number: int) -> Optional[dict]:
    """Récupère un cache de recherche s'il existe et n'est pas expiré.
    
    Args:
        db: Session de base de données
        city: Nom de la ville
        number: Nombre de résultats demandés
    
    Returns:
        Résultats en cache ou None si absent/expiré
    """
    city_key = city.strip().lower()
    cache_key = f"{city_key}:{number}"
    
    stmt = select(SearchCache).where(
        SearchCache.cache_key == cache_key,
        SearchCache.expires_at > datetime.now(timezone.utc)
    )
    cached = db.scalar(stmt)
    
    if cached:
        return cached.results
    
    return None


def set_cache(db: Session, city: str, number: int, params: dict, results: dict, ttl_hours: int = 24) -> SearchCache:
    """Enregistre un cache de recherche.
    
    Args:
        db: Session de base de données
        city: Nom de la ville
        number: Nombre de résultats
        params: Paramètres de recherche (pour debug/trace)
        results: Résultats à mettre en cache
        ttl_hours: Durée de vie du cache en heures (défaut: 24h)
    
    Returns:
        SearchCache créé ou mis à jour
    """
    city_key = city.strip().lower()
    cache_key = f"{city_key}:{number}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    
    # Chercher l'existant
    stmt = select(SearchCache).where(SearchCache.cache_key == cache_key)
    existing = db.scalar(stmt)
    
    if existing:
        existing.params = params
        existing.results = results
        existing.expires_at = expires_at
        db.commit()
        db.refresh(existing)
        return existing
    
    # Créer nouveau
    new_cache = SearchCache(
        cache_key=cache_key,
        city_key=city_key,
        params=params,
        results=results,
        expires_at=expires_at,
    )
    db.add(new_cache)
    db.commit()
    db.refresh(new_cache)
    return new_cache


def upsert_prospects(db: Session, prospects: List[dict], city_key: str) -> List[Prospect]:
    """Upsert (insert ou update) plusieurs prospects.
    
    Args:
        db: Session de base de données
        prospects: Liste de dictionnaires avec les données des prospects
        city_key: Clé de la ville (normalisée)
    
    Returns:
        Liste des prospects créés ou mis à jour
    """
    saved = []
    
    for prospect_data in prospects:
        osm_type = prospect_data.get("osm_type")
        osm_id = prospect_data.get("osm_id")
        
        if not osm_type or not osm_id:
            continue  # Skip si pas d'ID OSM
        
        # Chercher l'existant
        stmt = select(Prospect).where(
            Prospect.osm_type == osm_type,
            Prospect.osm_id == osm_id
        )
        existing = db.scalar(stmt)
        
        if existing:
            # Mettre à jour
            existing.city_key = city_key
            existing.name = prospect_data.get("name")
            existing.activity_type = prospect_data.get("activity_type")
            existing.activity_value = prospect_data.get("activity_value")
            existing.website = prospect_data.get("website")
            existing.emails = prospect_data.get("emails", [])
            existing.phones = prospect_data.get("phones", [])
            existing.stars = prospect_data.get("stars")
            existing.cuisine = prospect_data.get("cuisine")
            existing.opening_hours = prospect_data.get("opening_hours")
            existing.operator = prospect_data.get("operator")
            existing.brand = prospect_data.get("brand")
            existing.address = prospect_data.get("address")
            existing.lat = prospect_data.get("lat")
            existing.lon = prospect_data.get("lon")
            existing.osm_url = prospect_data.get("osm_url")
            existing.source = prospect_data.get("source", "OpenStreetMap")
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            saved.append(existing)
        else:
            # Créer nouveau
            new_prospect = Prospect(
                city_key=city_key,
                osm_type=osm_type,
                osm_id=osm_id,
                name=prospect_data.get("name"),
                activity_type=prospect_data.get("activity_type"),
                activity_value=prospect_data.get("activity_value"),
                website=prospect_data.get("website"),
                emails=prospect_data.get("emails", []),
                phones=prospect_data.get("phones", []),
                stars=prospect_data.get("stars"),
                cuisine=prospect_data.get("cuisine"),
                opening_hours=prospect_data.get("opening_hours"),
                operator=prospect_data.get("operator"),
                brand=prospect_data.get("brand"),
                address=prospect_data.get("address"),
                lat=prospect_data.get("lat"),
                lon=prospect_data.get("lon"),
                osm_url=prospect_data.get("osm_url"),
                source=prospect_data.get("source", "OpenStreetMap"),
            )
            db.add(new_prospect)
            db.commit()
            db.refresh(new_prospect)
            saved.append(new_prospect)
    
    return saved
