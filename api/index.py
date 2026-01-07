from time import perf_counter
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from prospect.osm import get_prospects
from prospect.enrich import enrich_prospects

app = FastAPI(title="Prospect.com API", version="0.2")

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
    where: str | None = Query(None, min_length=2, description="Ville/quartier/adresse/lieu..."),
    city: str | None = Query(None, min_length=2, description="Ancien paramètre (optionnel)."),
    lat: float | None = Query(None, ge=-90),
    lon: float | None = Query(None, ge=-180),
    radius_km: float | None = Query(None, gt=0),
    tags: str | None = Query(
        None,
        description=(
            "Filtres tags: "
            "ex 'restaurant,hotel,spa' "
            "ou 'amenity=restaurant,tourism=hotel,shop=bakery' "
            "ou 'amenity,shop,tourism'"
        ),
    ),
    number: int = Query(20, ge=1),
    enrich_max: int = Query(10, ge=0),
):
    if not (where or city or (lat is not None and lon is not None)):
        raise HTTPException(
            status_code=422,
            detail="Paramètres requis: where=... OU lat=...&lon=... (city accepté aussi).",
        )

    t_total0 = perf_counter()

    try:
        t_osm0 = perf_counter()
        results, meta = get_prospects(
            where=where,
            city=city,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            tags=tags,
            number=number,
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
    }

    if enrich_max > 0:
        t_en0 = perf_counter()
        results, enrich_meta = enrich_prospects(results, max_enrich=enrich_max, return_meta=True)
        enrich_seconds = perf_counter() - t_en0

    total_seconds = perf_counter() - t_total0

    return {
        "query": meta,
        "count": len(results),
        "enrich_max": enrich_max,
        "timings": {
            "total_seconds": round(total_seconds, 3),
            "osm_seconds": round(osm_seconds, 3),
            "enrichment_seconds": round(enrich_seconds, 3),
            "enrichment": enrich_meta,
        },
        "results": results,
    }
