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
    "https://overpass.openstreetmap.ru/api/interpreter",
    "https://overpass.osm.rambler.ru/cgi/interpreter",
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

    # Rate limiting pour Nominatim (1 requête par seconde max)
    time.sleep(1.0)
    
    try:
        r = session.get(NOMINATIM_URL, params=params, headers=headers, timeout=20)
        
        if r.status_code == 403:
            raise RuntimeError(
                "Nominatim 403 Forbidden. Causes fréquentes:\n"
                "  - VPN/proxy détecté\n"
                "  - IP limitée (trop de requêtes)\n"
                "Solutions: désactiver VPN, changer de réseau, attendre 10-30 min."
            )
        
        if r.status_code == 429:
            raise RuntimeError(
                "Nominatim rate limit (429). Trop de requêtes.\n"
                "Attendez 1-2 minutes et réessayez."
            )

        r.raise_for_status()
        data = r.json()
        
        if not data or len(data) == 0:
            raise RuntimeError(
                f"Ville '{city}' introuvable dans Nominatim.\n"
                "Essayez avec un nom plus spécifique (ex: 'Paris, France')."
            )

        south, north, west, east = map(float, data[0]["boundingbox"])
        bbox = (south, west, north, east)

        cache[key] = [south, west, north, east]
        _save_cache(cache)

        return bbox
    
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Timeout lors de la recherche de '{city}' dans Nominatim.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Erreur réseau Nominatim pour '{city}': {e}")


def _overpass_request(query: str, session: requests.Session) -> dict:
    """
    Fait une requête Overpass avec retry automatique sur plusieurs endpoints.
    """
    last_err = None
    errors_by_url = {}

    # Mélanger les endpoints pour répartir la charge
    endpoints = OVERPASS_ENDPOINTS.copy()
    random.shuffle(endpoints)

    for url in endpoints:
        for attempt in range(3):  # 3 tentatives par endpoint
            try:
                r = session.post(
                    url,
                    data=query,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                        "User-Agent": USER_AGENT,
                    },
                    timeout=60,  # Timeout augmenté pour les grandes villes
                )

                if r.status_code == 429:
                    # Rate limit - attendre plus longtemps
                    wait_time = (2 ** attempt) * 2 + random.random()
                    errors_by_url[url] = f"Rate limit (429), attente {wait_time:.1f}s"
                    time.sleep(wait_time)
                    continue

                if r.status_code != 200:
                    last_err = f"{url} HTTP {r.status_code}: {r.text[:200]}"
                    errors_by_url[url] = last_err
                    time.sleep((2 ** attempt) + random.random())
                    continue

                # Vérifier que la réponse est valide JSON
                try:
                    data = r.json()
                    if "elements" in data:
                        return data
                    else:
                        last_err = f"{url} réponse invalide: pas de 'elements'"
                        errors_by_url[url] = last_err
                except json.JSONDecodeError:
                    last_err = f"{url} réponse JSON invalide: {r.text[:200]}"
                    errors_by_url[url] = last_err
                    time.sleep((2 ** attempt) + random.random())
                    continue

            except requests.exceptions.Timeout:
                last_err = f"{url} timeout après 60s"
                errors_by_url[url] = last_err
                time.sleep((2 ** attempt) + random.random())
            except requests.exceptions.ConnectionError as e:
                last_err = f"{url} erreur de connexion: {e}"
                errors_by_url[url] = last_err
                time.sleep((2 ** attempt) + random.random())
            except Exception as e:
                last_err = f"{url}: {e}"
                errors_by_url[url] = last_err
                time.sleep((2 ** attempt) + random.random())

    # Tous les endpoints ont échoué
    error_summary = "\n".join([f"  - {url}: {err}" for url, err in errors_by_url.items()])
    raise RuntimeError(
        f"Tous les endpoints Overpass sont indisponibles.\n"
        f"Erreurs:\n{error_summary}\n"
        f"Vérifiez votre connexion internet et réessayez dans quelques minutes."
    )


def get_prospects(city: str, number: int = 20) -> list[dict]:
    """
    Récupère des prospects depuis OpenStreetMap pour une ville donnée.
    
    Args:
        city: Nom de la ville (ex: "Paris", "New York")
        number: Nombre de prospects à retourner (max recommandé: 100)
    
    Returns:
        Liste de dictionnaires contenant les informations des prospects
    """
    number = max(1, min(int(number), 200))  # Limite à 200 pour éviter les timeouts
    session = requests.Session()

    try:
        south, west, north, east = _get_bbox(city, session)
    except Exception as e:
        raise RuntimeError(f"Impossible de trouver les coordonnées de '{city}': {e}")

    # Requête Overpass améliorée avec plus de types de lieux
    # On demande plus de résultats pour avoir plus de choix après filtrage
    requested_count = min(number * 2, 500)
    
    query = f"""
    [out:json][timeout:60];
    (
      nwr["amenity"]["name"]({south},{west},{north},{east});
      nwr["shop"]["name"]({south},{west},{north},{east});
      nwr["tourism"]["name"]({south},{west},{north},{east});
      nwr["office"]["name"]({south},{west},{north},{east});
      nwr["craft"]["name"]({south},{west},{north},{east});
      nwr["leisure"]["name"]({south},{west},{north},{east});
      nwr["healthcare"]["name"]({south},{west},{north},{east});
      nwr["education"]["name"]({south},{west},{north},{east});
      nwr["historic"]["name"]({south},{west},{north},{east});
      nwr["aeroway"]["name"]({south},{west},{north},{east});
    );
    out center {requested_count};
    """

    try:
        data = _overpass_request(query, session)
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la requête Overpass pour '{city}': {e}")

    results = []
    seen_names = set()  # Éviter les doublons par nom

    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        
        # Filtrer les éléments sans nom ou déjà vus
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        
        # Filtrer les éléments sans coordonnées
        if not lat or not lon:
            continue

        # Déterminer le type d'activité (priorité aux types les plus pertinents)
        activity_key = None
        activity_value = None
        for k in ["amenity", "shop", "tourism", "office", "craft", "leisure", 
                  "healthcare", "education", "historic", "aeroway"]:
            if tags.get(k):
                activity_key = k
                activity_value = tags.get(k)
                break

        # Site web (plusieurs sources possibles)
        website = (
            tags.get("website") or 
            tags.get("contact:website") or 
            tags.get("url") or
            tags.get("contact:url")
        )

        # Emails
        emails = []
        for k in ["email", "contact:email", "contact:email_1", "contact:email_2"]:
            emails += _split_multi(tags.get(k, ""))
        emails = list(dict.fromkeys(emails))

        # Téléphones (plusieurs sources)
        phones = []
        for k in ["phone", "contact:phone", "mobile", "contact:mobile", 
                 "contact:whatsapp", "whatsapp", "contact:fax", "fax"]:
            phones += _split_multi(tags.get(k, ""))
        phones = list(dict.fromkeys(phones))

        # Adresse structurée
        address = {
            "housenumber": tags.get("addr:housenumber"),
            "street": tags.get("addr:street"),
            "postcode": tags.get("addr:postcode"),
            "city": tags.get("addr:city") or tags.get("addr:city:fr") or city,
            "country": tags.get("addr:country"),
        }

        # Informations supplémentaires
        stars = tags.get("stars") or tags.get("hotel:stars")
        opening_hours = tags.get("opening_hours")
        operator_ = tags.get("operator")
        brand = tags.get("brand")
        cuisine = tags.get("cuisine")
        
        # Description/résumé si disponible
        description = tags.get("description") or tags.get("note")

        # Lien OSM
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
        
        # Arrêter si on a assez de résultats
        if len(results) >= number:
            break

    return results[:number]
