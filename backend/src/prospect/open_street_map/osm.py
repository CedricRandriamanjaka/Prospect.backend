import json
import math
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
    "https://overpass.openstreetmap.ru/cgi/interpreter",
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
            # valeur seule => on tente sur toutes les clés (amenity/shop/...)
            out.append({"key": None, "value": t})

    if not out:
        return [{"key": k, "value": None} for k in ALL_KEYS]

    return out


def _geocode(where: str, session: requests.Session) -> Dict[str, Any]:
    key = where.strip().lower()

    cached = _bbox_cache_get(key)
    if isinstance(cached, dict) and "bbox" in cached and len(cached["bbox"]) == 4:
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

    time.sleep(1.0)  # respecter Nominatim

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
    """Fait une requête Overpass avec retry sur plusieurs endpoints."""
    errors_by_url = {}
    max_total_time = 40  # Timeout global de 40s max (strict)
    start_time = time.time()

    # Utiliser jusqu'à 5 endpoints pour plus de fiabilité (au lieu de 3)
    # On garde un timeout global pour éviter d'attendre trop longtemps
    endpoints = OVERPASS_ENDPOINTS[:3].copy()
    random.shuffle(endpoints)

    for url in endpoints:
        # Vérifier le timeout global avant chaque endpoint
        elapsed = time.time() - start_time
        if elapsed > max_total_time:
            break
            
        # Une seule tentative par endpoint pour aller plus vite
        try:
            remaining_time = max_total_time - elapsed
            request_timeout = min(25, max(5, remaining_time - 2))  # Laisser 2s de marge
            
            r = session.post(
                url,
                data=query,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                },
                timeout=request_timeout,
            )

            if r.status_code == 429:
                errors_by_url[url] = f"Rate limit (429)"
                continue

            if r.status_code != 200:
                errors_by_url[url] = f"HTTP {r.status_code}: {r.text[:200]}"
                continue

            try:
                data = r.json()
            except json.JSONDecodeError:
                errors_by_url[url] = f"JSON invalide: {r.text[:200]}"
                continue

            if "elements" in data:
                return data

            errors_by_url[url] = "Réponse invalide: pas de 'elements'"

        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            errors_by_url[url] = f"Timeout après {elapsed:.1f}s"
        except Exception as e:
            errors_by_url[url] = str(e)

    elapsed = time.time() - start_time
    error_summary = "\n".join([f"  - {url}: {err}" for url, err in errors_by_url.items()])
    raise RuntimeError(
        f"Tous les endpoints Overpass sont indisponibles (temps écoulé: {elapsed:.1f}s).\n"
        f"Erreurs:\n{error_summary}\n"
        "Réessayer dans quelques minutes ou réduire le rayon de recherche."
    )


def _contact_tag_variants(osm_has: Optional[list[str]]) -> list[list[str]]:
    """
    Retourne une liste de combinaisons de tags à exiger (AND),
    en gérant les variantes (OR) via produit cartésien.
    Ex:
      has=website,email => [
        ["website","email"], ["website","contact:email"], ["contact:website","email"], ...
      ]
    """
    if not osm_has:
        return []

    hs = set([h.strip().lower() for h in osm_has if h and h.strip()])
    if not hs:
        return []

    mapping: dict[str, list[str]] = {
        "website": ["website", "contact:website", "url", "contact:url"],
        "email": ["email", "contact:email"],
        "phone": ["phone", "contact:phone", "mobile", "contact:mobile"],
        "whatsapp": ["whatsapp", "contact:whatsapp"],
    }

    groups: list[list[str]] = []
    for k, variants in mapping.items():
        if k in hs:
            groups.append(variants)

    if not groups:
        return []

    # produit cartésien (cap de sécurité)
    combos: list[list[str]] = [[]]
    for g in groups:
        new: list[list[str]] = []
        for c in combos:
            for v in g:
                new.append(c + [v])
                if len(new) > 60:  # cap anti explosion
                    break
            if len(new) > 60:
                break
        combos = new
        if len(combos) > 60:
            combos = combos[:60]
            break

    return combos


def _filters_to_overpass_parts(
    filters: List[Dict[str, Optional[str]]],
    area_expr: str,
    osm_has: Optional[list[str]] = None,
) -> List[str]:
    parts: List[str] = []
    combos = _contact_tag_variants(osm_has)

    for f in filters:
        k = f.get("key")
        v = f.get("value")

        def emit(base: str):
            if combos:
                for combo in combos:
                    extra = "".join([f'["{t}"]' for t in combo])
                    parts.append(f'{base}{extra}["name"]{area_expr};')
            else:
                parts.append(f'{base}["name"]{area_expr};')

        if k and v:
            emit(f'nwr["{k}"="{v}"]')
        elif k and not v:
            emit(f'nwr["{k}"]')
        else:
            if not v:
                continue
            for kk in ALL_KEYS:
                emit(f'nwr["{kk}"="{v}"]')

    return parts


def _build_query_bbox(
    filters: List[Dict[str, Optional[str]]],
    south: float,
    west: float,
    north: float,
    east: float,
    limit: int,
    osm_has: Optional[list[str]] = None,
) -> str:
    area_expr = f"({south},{west},{north},{east})"
    parts = _filters_to_overpass_parts(filters, area_expr, osm_has=osm_has)
    body = "\n      ".join(parts)
    return f"""
    [out:json][timeout:25];
    (
      {body}
    );
    out center {limit};
    """


def _build_query_around(
    filters: List[Dict[str, Optional[str]]],
    lat: float,
    lon: float,
    radius_m: int,
    limit: int,
    osm_has: Optional[list[str]] = None,
) -> str:
    area_expr = f"(around:{radius_m},{lat},{lon})"
    parts = _filters_to_overpass_parts(filters, area_expr, osm_has=osm_has)
    body = "\n      ".join(parts)
    return f"""
    [out:json][timeout:25];
    (
      {body}
    );
    out center {limit};
    """


def _build_query_around_annulus(
    filters: List[Dict[str, Optional[str]]],
    lat: float,
    lon: float,
    min_radius_m: int,
    max_radius_m: int,
    limit: int,
    osm_has: Optional[list[str]] = None,
) -> str:
    """
    Anneau: max_radius - min_radius
    Renvoie uniquement ce qui est dans max_radius ET pas dans min_radius.
    
    NOTE: Cette requête est très lente sur Overpass. On utilise une approche simplifiée :
    on récupère tout dans max_radius et on filtre côté client (plus rapide).
    """
    # Approche simplifiée : récupérer tout dans max_radius, filtrer côté client
    area_expr = f"(around:{max_radius_m},{lat},{lon})"
    parts = _filters_to_overpass_parts(filters, area_expr, osm_has=osm_has)
    body = "\n      ".join(parts)
    return f"""
    [out:json][timeout:25];
    (
      {body}
    );
    out center {limit * 2};
    """


def _parse_elements(data: dict, fallback_city: str) -> list[dict]:
    results = []
    seen_entities = set()

    for el in data.get("elements", []):
        el_type = el.get("type", "node")
        el_id = el.get("id")

        # identifiant stable => dédup fiable
        if el_id is None:
            continue
        entity_key = f"osm:{el_type}:{el_id}"
        if entity_key in seen_entities:
            continue
        seen_entities.add(entity_key)

        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is None or lon is None:
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

        osm_link = f"https://www.openstreetmap.org/{el_type}/{el_id}"

        results.append({
            "entity_key": entity_key,   # utile pour DB
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
    radius_km: Optional[float] = None,          # rayon max
    radius_min_km: Optional[float] = None,      # rayon min (anneau)
    tags: Optional[str] = None,
    number: int = 20,
    osm_has: Optional[list[str]] = None,
) -> Tuple[List[dict], Dict[str, Any]]:
    """
    - Si radius_min_km est fourni et > 0, alors recherche en anneau:
      (radius_min_km, radius_km]
    - Sinon comportement standard.
    """
    number = max(1, min(int(number), 200))
    # Maintenant que toutes les requêtes utilisent des bbox (plus rapides), on peut utiliser le multiplicateur standard
    requested_count = min(number * 2, 500)

    s = requests.Session()
    query_text = (where or city or "").strip() or None
    filters = _parse_tags_param(tags)

    def _clamp_radius_km(v: float, minv: float, maxv: float) -> float:
        return max(minv, min(float(v), maxv))

    # -------------------------
    # Mode lat/lon direct
    # -------------------------
    if lat is not None and lon is not None:
        # OPTIMISATION: Convertir lat/lon + radius en bbox au lieu d'utiliser les requêtes "around"
        # Les requêtes "around" sont très lourdes et timeout facilement, surtout dans les zones denses
        # On utilise un bbox approximatif qui couvre le rayon demandé
        
        center_lat = float(lat)
        center_lon = float(lon)
        
        # Si radius_km est fourni, créer un bbox approximatif
        if radius_km is not None:
            used_max_km = _clamp_radius_km(radius_km, 0.2, 50.0)  # Max 50km pour éviter les bbox trop grands
            
            # Conversion approximative: 1 degré ≈ 111 km
            # Pour longitude, on ajuste selon la latitude
            delta_lat = used_max_km / 111.0
            delta_lon = used_max_km / (111.0 * math.cos(math.radians(center_lat)))
            
            south = center_lat - delta_lat
            north = center_lat + delta_lat
            west = center_lon - delta_lon
            east = center_lon + delta_lon
            
            # Clamp pour éviter les coordonnées invalides
            south = max(-90.0, min(90.0, south))
            north = max(-90.0, min(90.0, north))
            west = max(-180.0, min(180.0, west))
            east = max(-180.0, min(180.0, east))
            
            # Utiliser bbox au lieu de "around"
            q = _build_query_bbox(filters, south, west, north, east, requested_count, osm_has=osm_has)
            data = _overpass_request(q, s)
            results = _parse_elements(data, fallback_city=query_text or "coords")
            
            # Filtrer par distance côté client si radius_min_km est fourni (anneau)
            if radius_min_km is not None and radius_min_km > 0:
                used_min_km = _clamp_radius_km(radius_min_km, 0.0, used_max_km - 0.001)
                if used_min_km >= used_max_km:
                    raise ValueError("radius_min_km doit être strictement < radius_km")
                
                min_m_sq = (used_min_km * 1000) ** 2
                max_m_sq = (used_max_km * 1000) ** 2
                
                filtered_results = []
                for r in results:
                    r_lat = r.get("lat")
                    r_lon = r.get("lon")
                    if r_lat is None or r_lon is None:
                        continue
                    
                    # Distance approximative (formule de Haversine simplifiée)
                    dlat = math.radians(r_lat - center_lat)
                    dlon = math.radians(r_lon - center_lon)
                    a = math.sin(dlat/2)**2 + math.cos(math.radians(center_lat)) * math.cos(math.radians(r_lat)) * math.sin(dlon/2)**2
                    c = 2 * math.asin(math.sqrt(a))
                    distance_m = 6371000 * c
                    distance_m_sq = distance_m * distance_m
                    
                    # Garder si dans l'anneau (min < distance <= max)
                    if min_m_sq < distance_m_sq <= max_m_sq:
                        filtered_results.append(r)
                
                results = filtered_results
                mode = "latlon_bbox_annulus"
            else:
                mode = "latlon_bbox"
            
            meta = {
                "mode": mode,
                "where": query_text,
                "lat": lat,
                "lon": lon,
                "bbox": [south, west, north, east],
                "radius_km": used_max_km,
                "radius_min_km": radius_min_km if (radius_min_km is not None and radius_min_km > 0) else None,
                "tags": filters,
            }
            return results[:number], meta
        else:
            # Pas de radius_km: utiliser un petit bbox par défaut (1km)
            delta_lat = 1.0 / 111.0
            delta_lon = 1.0 / (111.0 * math.cos(math.radians(center_lat)))
            
            south = center_lat - delta_lat
            north = center_lat + delta_lat
            west = center_lon - delta_lon
            east = center_lon + delta_lon
            
            q = _build_query_bbox(filters, south, west, north, east, requested_count, osm_has=osm_has)
            data = _overpass_request(q, s)
            results = _parse_elements(data, fallback_city=query_text or "coords")
            
            meta = {
                "mode": "latlon_bbox",
                "where": query_text,
                "lat": lat,
                "lon": lon,
                "bbox": [south, west, north, east],
                "tags": filters,
            }
            return results[:number], meta

    # -------------------------
    # Mode where/city
    # -------------------------
    if not query_text:
        raise ValueError("Paramètres requis: where=... OU lat/lon.")

    geo = _geocode(query_text, s)

    # Si radius_km fourni => around (ou anneau)
    # OPTIMISATION: Si pas de filtres spécifiques (tags vide) OU si has est fourni, utiliser bbox au lieu de rayon
    # car les requêtes "around" sans filtres sont très lourdes et timeout facilement
    # et les requêtes "around" avec has génèrent beaucoup de combinaisons de tags qui multiplient les requêtes
    has_specific_filters = tags and tags.strip()
    # Si osm_has est fourni, on évite le mode "around" car ça génère trop de combinaisons
    use_bbox_instead = not has_specific_filters or (osm_has and len(osm_has) > 0)
    
    if radius_km is not None and has_specific_filters and not use_bbox_instead:
        # Limite réduite à 20km pour éviter les timeouts
        used_max_km = _clamp_radius_km(radius_km, 0.2, 20.0)
        used_min_km = _clamp_radius_km(radius_min_km, 0.0, 19.999) if radius_min_km is not None else 0.0

        if used_min_km >= used_max_km:
            raise ValueError("radius_min_km doit être strictement < radius_km")

        g_lat = geo.get("lat")
        g_lon = geo.get("lon")
        if g_lat is None or g_lon is None:
            south, west, north, east = map(float, geo["bbox"])
            g_lat = (south + north) / 2
            g_lon = (west + east) / 2

        max_m = int(used_max_km * 1000)
        min_m = int(used_min_km * 1000)

        if used_min_km > 0:
            q = _build_query_around_annulus(filters, float(g_lat), float(g_lon), min_m, max_m, requested_count, osm_has=osm_has)
            mode = "where+radius_annulus"
        else:
            q = _build_query_around(filters, float(g_lat), float(g_lon), max_m, requested_count, osm_has=osm_has)
            mode = "where+radius"

        data = _overpass_request(q, s)
        results = _parse_elements(data, fallback_city=query_text)
        
        # Filtrer l'anneau côté client si nécessaire (plus rapide que requête Overpass complexe)
        if used_min_km > 0:
            center_lat = float(g_lat)
            center_lon = float(g_lon)
            min_m_sq = min_m * min_m
            max_m_sq = max_m * max_m
            
            filtered_results = []
            for r in results:
                r_lat = r.get("lat")
                r_lon = r.get("lon")
                if r_lat is None or r_lon is None:
                    continue
                
                # Distance approximative (formule de Haversine simplifiée pour performance)
                dlat = math.radians(r_lat - center_lat)
                dlon = math.radians(r_lon - center_lon)
                a = math.sin(dlat/2)**2 + math.cos(math.radians(center_lat)) * math.cos(math.radians(r_lat)) * math.sin(dlon/2)**2
                c = 2 * math.asin(math.sqrt(a))
                distance_m = 6371000 * c  # Rayon Terre en mètres
                distance_m_sq = distance_m * distance_m
                
                # Garder si dans l'anneau (min < distance <= max)
                if min_m_sq < distance_m_sq <= max_m_sq:
                    filtered_results.append(r)
            
            results = filtered_results

        meta = {
            "mode": mode,
            "where": query_text,
            "display": geo.get("display"),
            "lat": g_lat,
            "lon": g_lon,
            "radius_km": used_max_km,
            "radius_min_km": used_min_km,
            "tags": filters,
            "geocode_cache_hit": bool(geo.get("cache_hit")),
        }
        return results[:number], meta

    # Sinon bbox
    south, west, north, east = map(float, geo["bbox"])
    q = _build_query_bbox(filters, south, west, north, east, requested_count, osm_has=osm_has)
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
