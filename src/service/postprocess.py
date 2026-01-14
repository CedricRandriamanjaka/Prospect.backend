from __future__ import annotations

import math
import random
import re
from typing import Any, Optional, Tuple
from urllib.parse import urlparse


def _csv(s: str | None) -> list[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def _norm_text(s: str | None) -> str:
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r"[\s\-_]+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _domain(url: str | None) -> str:
    if not url:
        return ""
    u = url.strip()
    if not u:
        return ""
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    try:
        netloc = urlparse(u).netloc.lower()
    except Exception:
        return ""
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def _norm_phone(p: str) -> str:
    if not p:
        return ""
    p = p.strip()
    # garde + et chiffres
    if p.startswith("+"):
        return "+" + re.sub(r"\D", "", p[1:])
    return re.sub(r"\D", "", p)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # rayon terre km
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _get_list(item: dict, key: str) -> list:
    v = item.get(key)
    if isinstance(v, list):
        return v
    return []


def compute_coverage(results: list[dict]) -> dict:
    total = len(results)
    has_site = sum(1 for r in results if (r.get("site") or "").strip())
    has_email = sum(1 for r in results if len(_get_list(r, "emails")) > 0)
    has_phone = sum(1 for r in results if len(_get_list(r, "telephones")) > 0)
    has_whatsapp = sum(1 for r in results if len(_get_list(r, "whatsapp")) > 0)
    contactable = sum(
        1
        for r in results
        if (r.get("site") or "").strip()
        or len(_get_list(r, "emails")) > 0
        or len(_get_list(r, "telephones")) > 0
        or len(_get_list(r, "whatsapp")) > 0
    )

    def pct(x: int) -> float:
        return round((x / total * 100.0), 1) if total > 0 else 0.0

    return {
        "total": total,
        "counts": {
            "has_site": has_site,
            "has_email": has_email,
            "has_phone": has_phone,
            "has_whatsapp": has_whatsapp,
            "contactable": contactable,
        },
        "percents": {
            "has_site": pct(has_site),
            "has_email": pct(has_email),
            "has_phone": pct(has_phone),
            "has_whatsapp": pct(has_whatsapp),
            "contactable": pct(contactable),
        },
    }


def add_sales_fields(
    results: list[dict],
    ref_point: Optional[Tuple[float, float]] = None,
) -> None:
    ref_lat, ref_lon = ref_point if ref_point else (None, None)

    for r in results:
        emails = _get_list(r, "emails")
        phones = _get_list(r, "telephones")
        wa = _get_list(r, "whatsapp")
        site = (r.get("site") or "").strip()

        r["sales"] = r.get("sales") or {}
        r["sales"]["domain"] = _domain(site)
        r["sales"]["emails_count"] = len(emails)
        r["sales"]["phones_count"] = len(phones)
        r["sales"]["whatsapp_count"] = len(wa)
        r["sales"]["contact_methods_count"] = int(bool(site)) + int(bool(emails)) + int(bool(phones)) + int(bool(wa))

        # contact principal
        primary = None
        if emails:
            primary = emails[0]
        elif phones:
            primary = phones[0]
        elif wa:
            primary = wa[0]
        elif site:
            primary = site
        r["sales"]["primary_contact"] = primary

        # distance
        if ref_lat is not None and ref_lon is not None:
            lat = r.get("lat")
            lon = r.get("lon")
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                r["sales"]["distance_km"] = round(_haversine_km(ref_lat, ref_lon, float(lat), float(lon)), 3)
            else:
                r["sales"]["distance_km"] = None
        else:
            r["sales"]["distance_km"] = None


def filter_results(
    results: list[dict],
    has: list[str],
    min_contacts: int,
    exclude_names: list[str],
    exclude_brands: list[str],
) -> list[dict]:
    has_set = set([h.lower() for h in has])

    out = []
    for r in results:
        name = (r.get("nom") or "")
        name_low = name.lower()

        # exclude names
        if exclude_names and any(x in name_low for x in exclude_names):
            continue

        # exclude brands (brand/operator/marque)
        brand_blob = " ".join(
            [
                str(r.get("marque") or ""),
                str(r.get("operateur") or ""),
                str(r.get("brand") or ""),
                str(r.get("operator") or ""),
            ]
        ).lower()
        if exclude_brands and any(x in brand_blob for x in exclude_brands):
            continue

        # has filters
        if has_set:
            if "website" in has_set and not (r.get("site") or "").strip():
                continue
            if "email" in has_set and len(_get_list(r, "emails")) == 0:
                continue
            if "phone" in has_set and len(_get_list(r, "telephones")) == 0:
                continue
            if "whatsapp" in has_set and len(_get_list(r, "whatsapp")) == 0:
                continue

        # min contacts
        c = (r.get("sales") or {}).get("contact_methods_count")
        if isinstance(c, int) and c < int(min_contacts):
            continue
        if not isinstance(c, int) and int(min_contacts) > 0:
            # si sales pas calculé (normalement non), on recalc minimal
            site = bool((r.get("site") or "").strip())
            emails = bool(_get_list(r, "emails"))
            phones = bool(_get_list(r, "telephones"))
            wa = bool(_get_list(r, "whatsapp"))
            if (int(site) + int(emails) + int(phones) + int(wa)) < int(min_contacts):
                continue

        out.append(r)

    return out


def sort_results(results: list[dict], sort: str, seed: int | None = None) -> list[dict]:
    s = (sort or "contacts").lower()

    if s == "random":
        rng = random.Random(seed)
        out = list(results)
        rng.shuffle(out)
        return out

    if s == "name":
        return sorted(results, key=lambda r: _norm_text(r.get("nom")))

    if s == "distance":
        # None en dernier
        return sorted(
            results,
            key=lambda r: (
                (r.get("sales") or {}).get("distance_km") is None,
                (r.get("sales") or {}).get("distance_km") or 0.0,
            ),
        )

    # default: contacts
    return sorted(
        results,
        key=lambda r: (
            -(r.get("sales") or {}).get("contact_methods_count", 0),
            -int(bool((r.get("site") or "").strip())),  # ✅ tie-break business
            -(r.get("sales") or {}).get("emails_count", 0),
            -(r.get("sales") or {}).get("phones_count", 0),
            _norm_text(r.get("nom")),
        ),
    )


def dedupe_results(results: list[dict], mode: str) -> tuple[list[dict], dict]:
    m = (mode or "smart").lower()
    if m == "none":
        return results, {"mode": "none", "removed": 0}

    seen = set()
    out = []

    def key_strict(r: dict) -> str:
        return (r.get("osm") or "").strip()

    def key_smart(r: dict) -> str:
        site = (r.get("site") or "").strip()
        dom = (r.get("sales") or {}).get("domain") or _domain(site)
        if dom:
            return "d:" + dom

        phones = _get_list(r, "telephones")
        if phones:
            return "p:" + _norm_phone(str(phones[0]))

        name = _norm_text(r.get("nom"))
        addr = r.get("adresse") or {}
        city = _norm_text(str(addr.get("city") or ""))
        street = _norm_text(str(addr.get("street") or ""))
        hn = _norm_text(str(addr.get("housenumber") or ""))
        return f"n:{name}|c:{city}|s:{street}|h:{hn}"

    kf = key_smart if m == "smart" else key_strict

    removed = 0
    for r in results:
        k = kf(r)
        if not k:
            out.append(r)
            continue
        if k in seen:
            removed += 1
            continue
        seen.add(k)
        out.append(r)

    return out, {"mode": m, "removed": removed}


def to_light_view(results: list[dict]) -> list[dict]:
    out = []
    for r in results:
        addr = r.get("adresse") or {}
        sales = r.get("sales") or {}
        out.append(
            {
                "nom": r.get("nom"),
                "activite_type": r.get("activite_type"),
                "activite_valeur": r.get("activite_valeur"),
                "site": r.get("site"),
                "primary_contact": sales.get("primary_contact"),
                "contact_methods_count": sales.get("contact_methods_count"),
                "distance_km": sales.get("distance_km"),
                "emails_count": sales.get("emails_count"),
                "phones_count": sales.get("phones_count"),
                "whatsapp_count": sales.get("whatsapp_count"),
                "city": addr.get("city"),
                "street": addr.get("street"),
                "postcode": addr.get("postcode"),
                "lat": r.get("lat"),
                "lon": r.get("lon"),
                "osm": r.get("osm"),
                "source": r.get("source"),
            }
        )
    return out


def category_to_tags(category: str | None) -> str | None:
    """
    Mapping simple "business" -> tags OSM.
    Tu peux enrichir cette table quand tu veux.
    """
    if not category:
        return None
    c = category.strip().lower()
    mapping = {
        "restaurant": "amenity=restaurant",
        "hotel": "tourism=hotel",
        "spa": "leisure=spa,amenity=spa",
        "bakery": "shop=bakery",
        "pharmacy": "amenity=pharmacy",
        "clinic": "amenity=clinic,healthcare=clinic",
        "dentist": "amenity=dentist,healthcare=dentist",
        "bar": "amenity=bar",
        "cafe": "amenity=cafe",
        "gym": "leisure=fitness_centre",
        "supermarket": "shop=supermarket",
        "hairdresser": "shop=hairdresser",
    }
    return mapping.get(c)


def postprocess(
    results: list[dict],
    *,
    has: str | None,
    min_contacts: int,
    exclude_names: str | None,
    exclude_brands: str | None,
    sort: str,
    dedupe: str,
    view: str,
    limit: int,
    ref_point: Optional[Tuple[float, float]] = None,
    seed: int | None = None,
) -> tuple[list[dict], dict, dict]:
    # 1) derive
    add_sales_fields(results, ref_point=ref_point)

    before = len(results)

    # 2) filters
    ex_names = [x.lower() for x in _csv(exclude_names)]
    ex_brands = [x.lower() for x in _csv(exclude_brands)]
    has_list = _csv(has)
    filtered = filter_results(results, has=has_list, min_contacts=min_contacts, exclude_names=ex_names, exclude_brands=ex_brands)

    after_filter = len(filtered)

    # 3) sort
    sorted_results = sort_results(filtered, sort=sort, seed=seed)

    # 4) dedupe (après tri => garde le “meilleur”)
    deduped, dd_meta = dedupe_results(sorted_results, mode=dedupe)

    # 5) limit final
    limited = deduped[: max(0, int(limit))] if limit else deduped

    # 6) coverage sur résultats finaux (plus utile côté business)
    coverage = compute_coverage(limited)

    meta = {
        "before": before,
        "after_filter": after_filter,
        "after_dedupe": len(deduped),
        "returned": len(limited),
        "sort": sort,
        "dedupe": dd_meta,
        "filters": {
            "has": has_list,
            "min_contacts": int(min_contacts),
            "exclude_names": ex_names,
            "exclude_brands": ex_brands,
        },
        "view": view,
    }

    if (view or "full").lower() == "light":
        return to_light_view(limited), meta, coverage

    return limited, meta, coverage
