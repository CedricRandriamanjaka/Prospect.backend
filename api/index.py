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
    # Texte libre
    where: str | None = Query(None, min_length=2, description="Ville/quartier/adresse/lieu..."),

    # Backward compatible (optionnel)
    city: str | None = Query(None, min_length=2, description="Ancien paramètre (optionnel)."),

    # Clic carte
    lat: float | None = Query(None, ge=-90),
    lon: float | None = Query(None, ge=-180),

    # Rayon
    radius_km: float | None = Query(None, gt=0),

    # Tags / filtres
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

    try:
        results, meta = get_prospects(
            where=where,
            city=city,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            tags=tags,
            number=number,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")

    if enrich_max > 0:
        results = enrich_prospects(results, max_enrich=enrich_max)

    return {
        "query": meta,
        "count": len(results),
        "enrich_max": enrich_max,
        "results": results,
    }
