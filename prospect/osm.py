import json
import time
import random
import re
import os
from threading import Lock
from typing import Optional, Dict, Any, List, Tuple

import requests

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://api.openstreetmap.fr/oapi/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
    "https://overpass.osm.rambler.ru/cgi/interpreter",
]

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

USER_AGENT = "prospect-com/0.1 (contact: randriamanjakacedric@gmail.com)"
CONTACT_EMAIL = "randriamanjakacedric@gmail.com"

ALL_KEYS = [
    "amenity",
    "shop",
    "tourism",
    "office",
    "craft",
    "leisure",
    "healthcare",
    "education",
    "historic",
    "aeroway",
]

# -------------------------
# Cache bbox en mémoire (pas de fichier)
# -------------------------
_BBOX_CACHE_TTL_SECONDS = int(os.getenv("BBOX_CACHE_TTL_SECONDS", "86400"))  # 24h par défaut
_BBOX_CACHE_MAX_ITEMS = int(os.getenv("BBOX_CACHE_MAX_ITEMS", "5000"))
_BBOX_CACHE: dict[str, tuple[float, dict]] = {}  # key -> (expires_at_epoch, value)
_BBOX_CACHE_LOCK = Lock()


def _bbox_cache_get(key: str) -> Optional[dict]:
    now = time.time()
    with _BBOX_CACHE_LOCK:
        item = _BBOX_CACHE.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at <= now:
            _BBOX_CACHE.pop(key, None)
            return None
        return value


def _bbox_cache_set(key: str, value: dict) -> None:
    now = time.time()
    expires_at = now + _BBOX_CACHE_TTL_SECONDS

    with _BBOX_CACHE_LOCK:
        _BBOX_CACHE[key] = (expires_at, value)

        # nettoyage : expirés d'abord
        if len(_BBOX_CACHE) > _BBOX_CACHE_MAX_ITEMS:
            for k, (exp, _) in list(_BBOX_CACHE.items()):
                if exp <= now:
                    _BBOX_CACHE.pop(k, None)

        # si toujours trop grand, éviction FIFO (ordre d’insertion dict)
        while len(_BBOX_CACHE) > _BBOX_CACHE_MAX_ITEMS:
            _BBOX_CACHE.pop(next(iter(_BBOX_CACHE)))


# -------------------------
# Utils
# -------------------------
def _split_multi(value: str) -> list[str]:
    if not value:
        return []
    v = value.strip()
    parts = re.split(r"[;,|/]+|\s{2,}", v)
    out = []
    for p in parts:
        p = p.strip()
        if p and p not in out:
            out.append(p)
    return out


def _parse_tags_param(tags: Optional[str]) -> List[Dict[str, Optional[str]]]:
    if not tags or not tags.strip():
        return [{"key": k, "value": None} for k in ALL_KEYS]

    out: List[Dict[str, Optional[str]]] = []
    for raw in tags.split(","):
        t = raw.strip()
        if not t:
            continue

        if "=" in t:
            k, v = t.split("=", 1)
            k = k.strip().lower()
            v = v.strip()
            if k not in ALL_KEYS:
                raise ValueError(f"Tag clé inconnue: '{k}'. Clés autorisées: {', '.join(ALL_KEYS)}")
            out.append({"key": k, "value": v})
            continue

        low = t.lower()
        if low in ALL_KEYS:
            out.append({"key": low, "value": None})
        else:
            out.append({"key": None, "value": t})

    if not out:
        return [{"key": k, "value": None} for k in ALL_KEYS]

    return out


def _geocode(where: str, session: requests.Session) -> Dict[str, Any]:
    key = where.strip().lower()

    cached = _bbox_cache_get(key)
    if isinstance(cached, dict) and "bbox" in cached and len(cached["bbox"]) == 4:
        # marquer le hit sans casser les usages existants
        out = dict(cached)
        out["cache_hit"] = True
        return out

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Referer": "https://prospect.local",
    }
    params = {
        "format": "jsonv2",
        "limit": 1,
        "q": where,
        "email": CONTACT_EMAIL,
        "addressdetails": 1,
    }

    time.sleep(1.0)

    try:
        r = session.get(NOMINATIM_URL, params=params, headers=headers, timeout=20)
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Timeout Nominatim pour '{where}'. Réessayer.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Erreur réseau Nominatim pour '{where}': {e}")

    if r.status_code == 403:
        raise RuntimeError(
            "Nominatim 403 Forbidden. Causes fréquentes: VPN/proxy, IP limitée. "
            "Solutions: désactiver VPN, changer de réseau, attendre 10-30 min."
        )
    if r.status_code == 429:
        raise RuntimeError("Nominatim rate limit (429). Attendre 1-2 minutes et réessayer.")
    if r.status_code >= 400:
        raise RuntimeError(f"Nominatim HTTP {r.status_code}: {r.text[:200]}")

    data = r.json()
    if not data:
        raise ValueError(f"Lieu introuvable: '{where}'. Essayer plus précis (ex: 'Paris, France').")

    item = data[0]
    south, north, west, east = map(float, item["boundingbox"])
    lat = float(item["lat"]) if "lat" in item else None
    lon = float(item["lon"]) if "lon" in item else None

    out = {
        "bbox": [south, west, north, east],
        "lat": lat,
        "lon": lon,
        "display": item.get("display_name") or where,
        "cache_hit": False,
    }

    _bbox_cache_set(key, out)
    return out


# -------------------------
# Overpass request (retry)
# -------------------------
def _overpass_request(query: str, session: requests.Session) -> dict:
    last_err = None
    errors_by_url = {}

    endpoints = OVERPASS_ENDPOINTS.copy()
    random.shuffle(endpoints)

    for url in endpoints:
        for attempt in range(3):
            try:
                r = session.post(
                    url,
                    data=query,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                        "User-Agent": USER_AGENT,
                    },
                    timeout=60,
                )

                if r.status_code == 429:
                    wait_time = (2 ** attempt) * 2 + random.random()
                    errors_by_url[url] = f"Rate limit (429), attente {wait_time:.1f}s"
                    time.sleep(wait_time)
                    continue

                if r.status_code != 200:
                    last_err = f"{url} HTTP {r.status_code}: {r.text[:200]}"
                    errors_by_url[url] = last_err
                    time.sleep((2 ** attempt) + random.random())
                    continue

                try:
                    data = r.json()
                    if "elements" in data:
                        return data
                    last_err = f"{url} réponse invalide: pas de 'elements'"
                    errors_by_url[url] = last_err
                except json.JSONDecodeError:
                    last_err = f"{url} JSON invalide: {r.text[:200]}"
                    errors_by_url[url] = last_err
                    time.sleep((2 ** attempt) + random.random())
                    continue

            except requests.exceptions.Timeout:
                last_err = f"{url} timeout après 60s"
                errors_by_url[url] = last_err
                time.sleep((2 ** attempt) + random.random())
            except Exception as e:
                last_err = f"{url}: {e}"
                errors_by_url[url] = last_err
                time.sleep((2 ** attempt) + random.random())

    error_summary = "\n".join([f"  - {url}: {err}" for url, err in errors_by_url.items()])
    raise RuntimeError(
        "Tous les endpoints Overpass sont indisponibles.\n"
        f"Erreurs:\n{error_summary}\n"
        "Réessayer dans quelques minutes."
    )


def _filters_to_overpass_parts(filters: List[Dict[str, Optional[str]]], area_expr: str) -> List[str]:
    parts: List[str] = []
    for f in filters:
        k = f.get("key")
        v = f.get("value")

        if k and v:
            parts.append(f'nwr["{k}"="{v}"]["name"]{area_expr};')
        elif k and not v:
            parts.append(f'nwr["{k}"]["name"]{area_expr};')
        else:
            if not v:
                continue
            for kk in ALL_KEYS:
                parts.append(f'nwr["{kk}"="{v}"]["name"]{area_expr};')

    return parts


def _build_query_bbox(filters: List[Dict[str, Optional[str]]], south: float, west: float, north: float, east: float, limit: int) -> str:
    area_expr = f"({south},{west},{north},{east})"
    parts = _filters_to_overpass_parts(filters, area_expr)
    body = "\n      ".join(parts)
    return f"""
    [out:json][timeout:60];
    (
      {body}
    );
    out center {limit};
    """


def _build_query_around(filters: List[Dict[str, Optional[str]]], lat: float, lon: float, radius_m: int, limit: int) -> str:
    area_expr = f"(around:{radius_m},{lat},{lon})"
    parts = _filters_to_overpass_parts(filters, area_expr)
    body = "\n      ".join(parts)
    return f"""
    [out:json][timeout:60];
    (
      {body}
    );
    out center {limit};
    """


def _parse_elements(data: dict, fallback_city: str) -> list[dict]:
    results = []
    seen_names = set()

    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if not lat or not lon:
            continue

        activity_key = None
        activity_value = None
        for k in ALL_KEYS:
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
        for k in ["phone", "contact:phone", "mobile", "contact:mobile",
                  "contact:whatsapp", "whatsapp", "contact:fax", "fax"]:
            phones += _split_multi(tags.get(k, ""))
        phones = list(dict.fromkeys(phones))

        address = {
            "housenumber": tags.get("addr:housenumber"),
            "street": tags.get("addr:street"),
            "postcode": tags.get("addr:postcode"),
            "city": tags.get("addr:city") or tags.get("addr:city:fr") or fallback_city,
            "country": tags.get("addr:country"),
        }

        stars = tags.get("stars") or tags.get("hotel:stars")
        opening_hours = tags.get("opening_hours")
        operator_ = tags.get("operator")
        brand = tags.get("brand")
        cuisine = tags.get("cuisine")

        el_type = el.get("type", "node")
        el_id = el.get("id")
        osm_link = f"https://www.openstreetmap.org/{el_type}/{el_id}" if el_id else None

        results.append({
            "nom": name,
            "activite_type": activity_key,
            "activite_valeur": activity_value,
            "site": website,
            "emails": emails,
            "telephones": phones,
            "etoiles": stars,
            "cuisine": cuisine,
            "horaires": opening_hours,
            "operateur": operator_,
            "marque": brand,
            "adresse": address,
            "lat": lat,
            "lon": lon,
            "osm": osm_link,
            "source": "OpenStreetMap",
        })

    return results


def get_prospects(
    where: Optional[str] = None,
    city: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_km: Optional[float] = None,
    tags: Optional[str] = None,
    number: int = 20,
) -> Tuple[List[dict], Dict[str, Any]]:
    number = max(1, min(int(number), 200))
    requested_count = min(number * 2, 500)

    s = requests.Session()
    query_text = (where or city or "").strip() or None

    filters = _parse_tags_param(tags)

    if lat is not None and lon is not None:
        used_radius_km = float(radius_km) if radius_km is not None else 5.0
        used_radius_km = max(0.2, min(used_radius_km, 50.0))
        radius_m = int(used_radius_km * 1000)

        q = _build_query_around(filters, float(lat), float(lon), radius_m, requested_count)
        data = _overpass_request(q, s)
        results = _parse_elements(data, fallback_city=query_text or "coords")

        meta = {
            "mode": "around",
            "where": query_text,
            "lat": lat,
            "lon": lon,
            "radius_km": used_radius_km,
            "tags": filters,
        }
        return results[:number], meta

    if not query_text:
        raise ValueError("Paramètres requis: where=... OU lat/lon.")

    geo = _geocode(query_text, s)

    if radius_km is not None:
        used_radius_km = max(0.2, min(float(radius_km), 50.0))
        radius_m = int(used_radius_km * 1000)

        g_lat = geo.get("lat")
        g_lon = geo.get("lon")
        if g_lat is None or g_lon is None:
            south, west, north, east = map(float, geo["bbox"])
            g_lat = (south + north) / 2
            g_lon = (west + east) / 2

        q = _build_query_around(filters, float(g_lat), float(g_lon), radius_m, requested_count)
        data = _overpass_request(q, s)
        results = _parse_elements(data, fallback_city=query_text)

        meta = {
            "mode": "where+radius",
            "where": query_text,
            "display": geo.get("display"),
            "lat": g_lat,
            "lon": g_lon,
            "radius_km": used_radius_km,
            "tags": filters,
            "geocode_cache_hit": bool(geo.get("cache_hit")),
        }
        return results[:number], meta

    south, west, north, east = map(float, geo["bbox"])
    q = _build_query_bbox(filters, south, west, north, east, requested_count)
    data = _overpass_request(q, s)
    results = _parse_elements(data, fallback_city=query_text)

    meta = {
        "mode": "bbox",
        "where": query_text,
        "display": geo.get("display"),
        "bbox": [south, west, north, east],
        "tags": filters,
        "geocode_cache_hit": bool(geo.get("cache_hit")),
    }
    return results[:number], meta
