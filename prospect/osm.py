import json
import time
import random
import re
from pathlib import Path
import requests

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://api.openstreetmap.fr/oapi/interpreter",
]

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
CACHE_FILE = "bbox_cache.json"

USER_AGENT = "prospect-com/0.1 (contact: randriamanjakacedric@gmail.com)"
CONTACT_EMAIL = "randriamanjakacedric@gmail.com"


def _load_cache() -> dict:
    p = Path(CACHE_FILE)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    Path(CACHE_FILE).write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


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


def _get_bbox(city: str, session: requests.Session) -> tuple[float, float, float, float]:
    key = city.strip().lower()
    cache = _load_cache()

    if key in cache and len(cache[key]) == 4:
        s, w, n, e = cache[key]
        return float(s), float(w), float(n), float(e)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Referer": "https://prospect.local",
    }
    params = {
        "format": "jsonv2",
        "limit": 1,
        "q": city,
        "email": CONTACT_EMAIL,
    }

    time.sleep(1.0)
    r = session.get(NOMINATIM_URL, params=params, headers=headers, timeout=20)

    if r.status_code == 403:
        raise RuntimeError(
            "Nominatim 403. Causes fréquentes: VPN/proxy, IP limitée. "
            "Essayer sans VPN, changer de réseau, attendre 10-30 min."
        )

    r.raise_for_status()
    data = r.json()
    if not data:
        raise RuntimeError(f"Ville introuvable: {city}")

    south, north, west, east = map(float, data[0]["boundingbox"])
    bbox = (south, west, north, east)

    cache[key] = [south, west, north, east]
    _save_cache(cache)

    return bbox


def _overpass_request(query: str, session: requests.Session) -> dict:
    last_err = None

    for url in OVERPASS_ENDPOINTS:
        for attempt in range(2):
            try:
                r = session.post(
                    url,
                    data=query,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                    },
                    timeout=45,
                )

                if r.status_code != 200:
                    last_err = f"{url} HTTP {r.status_code}: {r.text[:200]}"
                    time.sleep((2 ** attempt) + random.random())
                    continue

                return r.json()

            except Exception as e:
                last_err = f"{url}: {e}"
                time.sleep((2 ** attempt) + random.random())

    raise RuntimeError(f"Overpass indisponible. Dernière erreur: {last_err}")


def get_prospects(city: str, number: int = 20) -> list[dict]:
    number = max(1, int(number))
    session = requests.Session()

    south, west, north, east = _get_bbox(city, session)

    query = f"""
    [out:json][timeout:25];
    (
      nwr["amenity"]["name"]({south},{west},{north},{east});
      nwr["shop"]["name"]({south},{west},{north},{east});
      nwr["tourism"]["name"]({south},{west},{north},{east});
      nwr["office"]["name"]({south},{west},{north},{east});
      nwr["craft"]["name"]({south},{west},{north},{east});
      nwr["leisure"]["name"]({south},{west},{north},{east});
    );
    out center {number};
    """

    data = _overpass_request(query, session)
    results = []

    for el in data.get("elements", []):
        tags = el.get("tags", {})

        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")

        activity_key = None
        for k in ["amenity", "shop", "tourism", "office", "craft", "leisure"]:
            if tags.get(k):
                activity_key = k
                break
        activity_value = tags.get(activity_key) if activity_key else None

        website = tags.get("website") or tags.get("contact:website") or tags.get("url")

        emails = []
        for k in ["email", "contact:email"]:
            emails += _split_multi(tags.get(k, ""))
        emails = list(dict.fromkeys(emails))

        phones = []
        for k in ["phone", "contact:phone", "mobile", "contact:mobile", "contact:whatsapp", "whatsapp"]:
            phones += _split_multi(tags.get(k, ""))
        phones = list(dict.fromkeys(phones))

        address = {
            "housenumber": tags.get("addr:housenumber"),
            "street": tags.get("addr:street"),
            "postcode": tags.get("addr:postcode"),
            "city": tags.get("addr:city"),
            "country": tags.get("addr:country"),
        }

        stars = tags.get("stars") or tags.get("hotel:stars")
        opening_hours = tags.get("opening_hours")
        operator_ = tags.get("operator")
        brand = tags.get("brand")
        cuisine = tags.get("cuisine")

        osm_link = f"https://www.openstreetmap.org/{el.get('type')}/{el.get('id')}"

        results.append({
            "nom": tags.get("name"),
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

    return results[:number]
