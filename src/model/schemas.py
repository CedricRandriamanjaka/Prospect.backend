"""Schémas Pydantic pour l'API."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AdresseSchema(BaseModel):
    """Schéma pour l'adresse d'un prospect."""
    housenumber: Optional[str] = None
    street: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProspectBase(BaseModel):
    """Schéma de base pour un prospect."""
    name: Optional[str] = None
    activity_type: Optional[str] = None
    activity_value: Optional[str] = None
    website: Optional[str] = None
    emails: List[str] = []
    phones: List[str] = []
    stars: Optional[str] = None
    cuisine: Optional[str] = None
    opening_hours: Optional[str] = None
    operator: Optional[str] = None
    brand: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    osm_url: Optional[str] = None
    source: Optional[str] = "OpenStreetMap"


class ProspectResponse(ProspectBase):
    """Schéma de réponse pour un prospect."""
    id: str
    city_key: str
    osm_type: str
    osm_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProspectsListResponse(BaseModel):
    """Schéma de réponse pour une liste de prospects."""
    city: str
    count: int
    results: List[ProspectResponse]
