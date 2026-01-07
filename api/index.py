from time import perf_counter
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from prospect.osm import get_prospects
from prospect.enrich import enrich_prospects
from prospect.postprocess import postprocess, category_to_tags

app = FastAPI(title="Prospect.com API", version="0.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/prospects")
def prospects(
    # Texte libre
    where: str | None = Query(None, min_length=2, description="Ville/quartier/adresse/lieu..."),
    # Backward compatible
    city: str | None = Query(None, min_length=2, description="Ancien paramètre (optionnel)."),

    # Clic carte
    lat: float | None = Query(None, ge=-90),
    lon: float | None = Query(None, ge=-180),

    # Rayon
    radius_km: float | None = Query(None, gt=0),

    # Tags / filtres OSM
    tags: str | None = Query(
        None,
        description=(
            "Filtres tags: "
            "ex 'restaurant,hotel,spa' "
            "ou 'amenity=restaurant,tourism=hotel,shop=bakery' "
            "ou 'amenity,shop,tourism'"
        ),
    ),

    # Catégorie business simple (optionnel)
    category: str | None = Query(None, description="Ex: restaurant, hotel, spa, bakery, pharmacy..."),

    # Nombre final renvoyé
    number: int = Query(20, ge=1, le=200),

    # Enrichissement
    enrich_max: int = Query(10, ge=0, le=200),
    enrich_mode: str = Query("missing", description="missing|always|never"),

    # Filtres prospection
    has: str | None = Query(None, description="Ex: website,email,phone,whatsapp"),
    min_contacts: int = Query(0, ge=0, le=4),
    exclude_names: str | None = Query(None, description="Mots à exclure dans nom. Ex: mairie, police"),
    exclude_brands: str | None = Query(None, description="Exclure marque/opérateur. Ex: kfc, carrefour"),

    # Tri / dédup
    sort: str = Query("contacts", description="contacts|distance|name|random"),
    dedupe: str = Query("smart", description="none|strict|smart"),
    seed: int | None = Query(None, description="Seed pour sort=random"),

    # Vue
    view: str = Query("full", description="full|light"),

    # Stats
    include_coverage: bool = Query(True),
):
    if not (where or city or (lat is not None and lon is not None)):
        raise HTTPException(
            status_code=422,
            detail="Paramètres requis: where=... OU lat=...&lon=... (city accepté aussi).",
        )

    t_total0 = perf_counter()

    # category -> tags (si tags non fourni)
    if (not tags or not tags.strip()) and category:
        mapped = category_to_tags(category)
        if mapped:
            tags = mapped

    # Astuce: on récupère plus que number pour permettre filtrage/dedupe sans tomber à 3 résultats
    fetch_number = min(max(int(number) * 3, int(number)), 200)

    try:
        t_osm0 = perf_counter()
        results_raw, meta = get_prospects(
            where=where,
            city=city,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            tags=tags,
            number=fetch_number,
        )
        osm_seconds = perf_counter() - t_osm0
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")

    enrich_seconds = 0.0
    enrich_meta = {
        "enriched_count": 0,
        "total_seconds": 0.0,
        "avg_seconds": 0.0,
        "per_item": [],
        "max_enrich": enrich_max,
        "mode": enrich_mode,
    }

    # Enrichissement selon mode
    if enrich_max > 0 and (enrich_mode or "").lower() != "never":
        t_en0 = perf_counter()
        mode = (enrich_mode or "missing").lower()
        results_raw, enrich_meta = enrich_prospects(
            results_raw,
            max_enrich=enrich_max,
            return_meta=True,
            mode=mode,
        )
        enrich_seconds = perf_counter() - t_en0

    # Point de référence pour distance
    ref_point = None
    try:
        if lat is not None and lon is not None:
            ref_point = (float(lat), float(lon))
        else:
            # si meta a bbox => centre
            bbox = meta.get("bbox")
            if isinstance(bbox, list) and len(bbox) == 4:
                s, w, n, e = map(float, bbox)
                ref_point = ((s + n) / 2.0, (w + e) / 2.0)
            else:
                # si meta a lat/lon (where+radius)
                ml = meta.get("lat")
                mn = meta.get("lon")
                if isinstance(ml, (int, float)) and isinstance(mn, (int, float)):
                    ref_point = (float(ml), float(mn))
    except Exception:
        ref_point = None

    # Post-process: filtres / tri / dedupe / view + coverage
    t_pp0 = perf_counter()
    results_final, pp_meta, coverage = postprocess(
        results_raw,
        has=has,
        min_contacts=min_contacts,
        exclude_names=exclude_names,
        exclude_brands=exclude_brands,
        sort=sort,
        dedupe=dedupe,
        view=view,
        limit=number,
        ref_point=ref_point,
        seed=seed,
    )
    postprocess_seconds = perf_counter() - t_pp0

    total_seconds = perf_counter() - t_total0

    resp = {
        "query": meta,
        "requested": {
            "number": number,
            "fetched_before_filters": len(results_raw),
        },
        "count": len(results_final),
        "enrich_max": enrich_max,
        "enrich_mode": enrich_mode,
        "postprocess": pp_meta,
        "timings": {
            "total_seconds": round(total_seconds, 3),
            "osm_seconds": round(osm_seconds, 3),
            "enrichment_seconds": round(enrich_seconds, 3),
            "postprocess_seconds": round(postprocess_seconds, 3),
            "enrichment": enrich_meta,
        },
        "results": results_final,
    }

    if include_coverage:
        resp["coverage"] = coverage

    return resp
