from __future__ import annotations

import json
import math
import os
import random
import re
import time
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import requests


# --- Endpoints (1 Overpass)
OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
NOMINATIM_URL = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")

CONTACT_EMAIL = os.getenv("OSM_CONTACT_EMAIL", "randriamanjakacedric@gmail.com")
USER_AGENT = os.getenv("OSM_USER_AGENT", f"prospecting/1.0 (contact: {CONTACT_EMAIL})")

# Clés “POI” courantes (si user donne des valeurs seules)
DEFAULT_POI_KEYS = ["amenity", "shop", "tourism", "leisure", "office", "craft", "healthcare"]

# Gardes-fous anti-overpass
MAX_RADIUS_KM = float(os.getenv("OSM_MAX_RADIUS_KM", "25"))
MAX_LIMIT = 200

_SAFE_KEY_RE = re.compile(r"^[A-Za-z0-9:_-]+$")

# Cache geocode
_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_LOCK = Lock()
CACHE_TTL = int(os.getenv("OSM_GEOCODE_CACHE_TTL", "86400"))  # 24h

# Rate limit Nominatim (≈1 req/s)
_LAST_NOMINATIM = 0.0
_NOMINATIM_LOCK = Lock()


def _rate_limit_nominatim(min_interval: float = 1.0) -> None:
    global _LAST_NOMINATIM
    with _NOMINATIM_LOCK:
        now = time.time()
        wait = min_interval - (now - _LAST_NOMINATIM)
        if wait > 0:
            time.sleep(wait)
        _LAST_NOMINATIM = time.time()


def _cache_get(key: str) -> Optional[dict]:
    now = time.time()
    with _CACHE_LOCK:
        it = _CACHE.get(key)
        if not it:
            return None
        exp, val = it
        if exp <= now:
            _CACHE.pop(key, None)
            return None
        return val


def _cache_set(key: str, val: dict) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = (time.time() + CACHE_TTL, val)


def _escape_ql_string(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")


def _safe_key(k: str) -> str:
    k = (k or "").strip()
    if not k or not _SAFE_KEY_RE.match(k):
        raise ValueError(f"Tag key invalide: '{k}'")
    return k


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _bbox_around(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    radius_km = max(0.2, min(float(radius_km), MAX_RADIUS_KM))
    delta_lat = radius_km / 111.0
    cos_lat = max(0.2, abs(math.cos(math.radians(lat))))
    delta_lon = radius_km / (111.0 * cos_lat)

    south = max(-90.0, lat - delta_lat)
    north = min(90.0, lat + delta_lat)
    west = max(-180.0, lon - delta_lon)
    east = min(180.0, lon + delta_lon)
    return south, west, north, east


def _geocode(where: str, session: requests.Session) -> dict:
    q = (where or "").strip()
    if len(q) < 2:
        raise ValueError("where trop court")

    key = q.lower()
    cached = _cache_get(key)
    if cached:
        return {**cached, "cache_hit": True}

    _rate_limit_nominatim(1.0)

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    params = {"format": "jsonv2", "limit": 1, "q": q, "email": CONTACT_EMAIL, "addressdetails": 1}

    try:
        r = session.get(NOMINATIM_URL, params=params, headers=headers, timeout=20)
    except requests.exceptions.Timeout:
        raise RuntimeError("Timeout Nominatim (geocoding).")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Erreur réseau Nominatim: {e}")

    if r.status_code == 429:
        raise RuntimeError("Nominatim rate limit (429). Réessaye plus tard.")
    if r.status_code >= 400:
        raise RuntimeError(f"Nominatim HTTP {r.status_code}: {r.text[:200]}")

    data = r.json()
    if not data:
        raise ValueError(f"Lieu introuvable: '{q}'")

    it = data[0]
    south, north, west, east = map(float, it["boundingbox"])
    out = {
        "display": it.get("display_name") or q,
        "lat": float(it["lat"]),
        "lon": float(it["lon"]),
        "bbox": [south, west, north, east],
    }

    _cache_set(key, out)
    return {**out, "cache_hit": False}


def _parse_tags(tags: Optional[str]) -> list[dict]:
    """
    Supporte:
    - key=value
    - key (uniquement si key ∈ DEFAULT_POI_KEYS)  -> existence
    - valeur seule -> testée sur DEFAULT_POI_KEYS
    """
    if not tags or not tags.strip():
        # “n’importe quel point POI” (mais ça doit rester petit rayon sinon Overpass peut exploser)
        return [{"type": "key_exists", "key": k} for k in DEFAULT_POI_KEYS]

    out = []
    for raw in tags.split(","):
        t = raw.strip()
        if not t:
            continue

        if "=" in t:
            k, v = t.split("=", 1)
            k = _safe_key(k.strip())
            v = v.strip()
            if not v:
                out.append({"type": "key_exists", "key": k})
            else:
                out.append({"type": "kv", "key": k, "value": v})
            continue

        low = t.lower()
        if low in DEFAULT_POI_KEYS:
            out.append({"type": "key_exists", "key": low})
        else:
            # valeur seule
            out.append({"type": "value_only", "value": t})

    return out or [{"type": "key_exists", "key": k} for k in DEFAULT_POI_KEYS]


def _build_overpass_query(filters: list[dict], south: float, west: float, north: float, east: float, fetch_limit: int) -> str:
    bbox = f"({south},{west},{north},{east})"
    lines: list[str] = []

    for f in filters:
        if f["type"] == "kv":
            k = f["key"]
            v = _escape_ql_string(f["value"])
            lines.append(f'nwr["{k}"="{v}"]["name"]{bbox};')
        elif f["type"] == "key_exists":
            k = f["key"]
            lines.append(f'nwr["{k}"]["name"]{bbox};')
        elif f["type"] == "value_only":
            v = _escape_ql_string(f["value"])
            for k in DEFAULT_POI_KEYS:
                lines.append(f'nwr["{k}"="{v}"]["name"]{bbox};')

    body = "\n  ".join(lines)

    return f"""[out:json][timeout:25];
(
  {body}
);
out center {int(fetch_limit)};
"""


def _overpass_request(query: str, session: requests.Session) -> dict:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    attempts = 3
    backoff = 2.0
    last_err = None

    for i in range(attempts):
        try:
            r = session.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=35)
            if r.status_code == 429:
                last_err = "Overpass rate limit (429)"
                time.sleep(backoff + random.random())
                backoff *= 2
                continue
            if r.status_code >= 500:
                last_err = f"Overpass HTTP {r.status_code}"
                time.sleep(backoff + random.random())
                backoff *= 2
                continue
            if r.status_code != 200:
                raise RuntimeError(f"Overpass HTTP {r.status_code}: {r.text[:200]}")
            return r.json()
        except requests.exceptions.Timeout:
            last_err = "Overpass timeout"
            time.sleep(backoff + random.random())
            backoff *= 2
        except json.JSONDecodeError:
            last_err = "Overpass JSON invalide"
            time.sleep(backoff + random.random())
            backoff *= 2
        except Exception as e:
            last_err = str(e)
            time.sleep(backoff + random.random())
            backoff *= 2

    raise RuntimeError(
        f"Overpass indisponible sur {OVERPASS_URL} après {attempts} tentatives. "
        f"Cause probable: zone trop grande / filtre trop large. Dernière erreur: {last_err}. "
        f"Solution: réduire radius_km, ajouter category/tags, ou baisser limit."
    )


def _split_multi(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[;,|/]+|\s{2,}", value.strip())
    out = []
    for p in parts:
        p = p.strip()
        if p and p not in out:
            out.append(p)
    return out


def _parse_elements(data: dict) -> list[dict]:
    out = []
    seen = set()

    for el in data.get("elements", []):
        el_type = el.get("type", "node")
        el_id = el.get("id")
        if el_id is None:
            continue

        entity_key = f"osm:{el_type}:{el_id}"
        if entity_key in seen:
            continue
        seen.add(entity_key)

        tags = (el.get("tags") or {})
        name = tags.get("name")
        if not name:
            continue

        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue

        # activity type/value (première clé reconnue)
        activity_key = None
        activity_value = None
        for k in DEFAULT_POI_KEYS:
            if tags.get(k):
                activity_key = k
                activity_value = tags.get(k)
                break

        website = (
            tags.get("website")
            or tags.get("contact:website")
            or tags.get("url")
            or tags.get("contact:url")
        )

        emails = []
        for k in ["email", "contact:email", "contact:email_1", "contact:email_2"]:
            emails += _split_multi(tags.get(k, ""))
        emails = list(dict.fromkeys(emails))

        phones = []
        for k in ["phone", "contact:phone", "mobile", "contact:mobile", "fax", "contact:fax"]:
            phones += _split_multi(tags.get(k, ""))
        phones = list(dict.fromkeys(phones))

        whatsapp = []
        for k in ["whatsapp", "contact:whatsapp"]:
            whatsapp += _split_multi(tags.get(k, ""))
        whatsapp = list(dict.fromkeys(whatsapp))

        address = {
            "housenumber": tags.get("addr:housenumber"),
            "street": tags.get("addr:street"),
            "postcode": tags.get("addr:postcode"),
            "city": tags.get("addr:city") or tags.get("addr:city:fr"),
            "country": tags.get("addr:country"),
        }

        stars = tags.get("stars") or tags.get("hotel:stars")
        opening_hours = tags.get("opening_hours")
        operator_ = tags.get("operator")
        brand = tags.get("brand")
        cuisine = tags.get("cuisine")

        out.append({
            "entity_key": entity_key,
            "nom": name,
            "activite_type": activity_key,
            "activite_valeur": activity_value,
            "site": website,
            "emails": emails,
            "telephones": phones,
            "whatsapp": whatsapp,
            "etoiles": stars,
            "cuisine": cuisine,
            "horaires": opening_hours,
            "operateur": operator_,
            "marque": brand,
            "adresse": address,
            "lat": float(lat),
            "lon": float(lon),
            "osm": f"https://www.openstreetmap.org/{el_type}/{el_id}",
            "source": "OpenStreetMap",
            "raw_tags": tags,  # optionnel: utile si tu veux tout garder
        })

    return out


def get_prospects(
    *,
    where: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    radius_km: Optional[float],
    radius_min_km: Optional[float],
    tags: Optional[str],
    limit: int,
) -> Tuple[List[dict], Dict[str, Any]]:
    limit = max(1, min(int(limit), MAX_LIMIT))
    session = requests.Session()

    t0 = time.perf_counter()

    # --- centre + bbox
    if lat is not None and lon is not None:
        center_lat = float(lat)
        center_lon = float(lon)
    else:
        if not where or not where.strip():
            raise ValueError("Tu dois fournir where OU lat/lon.")
        geo = _geocode(where.strip(), session)
        center_lat = float(geo["lat"])
        center_lon = float(geo["lon"])

    # radius_km (obligatoire en pratique pour stabilité si tags est large)
    if radius_km is None:
        # Sans radius, risque de zone énorme => Overpass errors.
        raise ValueError("radius_km est requis (pour éviter les erreurs Overpass). Exemple: radius_km=2")

    max_km = max(0.2, min(float(radius_km), MAX_RADIUS_KM))
    min_km = max(0.0, float(radius_min_km or 0.0))
    if min_km > 0 and min_km >= max_km:
        raise ValueError("radius_min_km doit être strictement < radius_km.")

    south, west, north, east = _bbox_around(center_lat, center_lon, max_km)

    # --- filtres (category->tags déjà fait au controller si besoin)
    parsed = _parse_tags(tags)

    # fetch_limit: on récupère un peu plus pour l’anneau (sinon tu risques d’avoir 0 résultats)
    fetch_limit = min(1000, max(limit * 3, limit))

    query = _build_overpass_query(parsed, south, west, north, east, fetch_limit)

    t_over = time.perf_counter()
    data = _overpass_request(query, session)
    over_s = time.perf_counter() - t_over

    results = _parse_elements(data)

    # --- filtre anneau (min/max) côté serveur impossible proprement => on le fait ici (léger)
    if min_km > 0:
        filtered = []
        for r in results:
            d = _haversine_km(center_lat, center_lon, float(r["lat"]), float(r["lon"]))
            if (d > min_km) and (d <= max_km):
                filtered.append(r)
        results = filtered
    else:
        # filtre max_km exact (bbox est approx)
        filtered = []
        for r in results:
            d = _haversine_km(center_lat, center_lon, float(r["lat"]), float(r["lon"]))
            if d <= max_km:
                filtered.append(r)
        results = filtered

    results = results[:limit]

    meta = {
        "where": where,
        "lat": center_lat,
        "lon": center_lon,
        "radius_km": max_km,
        "radius_min_km": min_km if min_km > 0 else None,
        "bbox": [south, west, north, east],
        "tags": tags,
        "overpass_endpoint": OVERPASS_URL,
        "timings": {
            "overpass_seconds": round(over_s, 3),
            "provider_total_seconds": round(time.perf_counter() - t0, 3),
        },
    }
    return results, meta
