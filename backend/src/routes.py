from time import perf_counter
from fastapi import APIRouter, Query, HTTPException

from src.controller.prospect_controller import ProspectController

router = APIRouter()


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/prospects")
def prospects(
    # Localisation
    where: str | None = Query(None, min_length=2, description="Champ libre localisation (ville/adresse/lieu…)"),
    lat: float | None = Query(None, ge=-90, le=90, description="Latitude (point manuel)"),
    lon: float | None = Query(None, ge=-180, le=180, description="Longitude (point manuel)"),

    # Rayon
    radius_km: float | None = Query(None, gt=0, description="km max"),
    radius_min_km: float | None = Query(None, ge=0, description="km min (anneau)"),

    # Filtre métier
    category: str | None = Query(None, description="Ex: restaurant, spa, hotel…"),
    tags: str | None = Query(
        None,
        description=(
            "Filtre OSM: "
            "ex 'amenity=restaurant' ou 'shop=bakery,tourism=hotel' "
            "ou 'amenity,shop,tourism' (clés) "
            "ou 'restaurant,spa' (valeurs)"
        ),
    ),

    # Résultats
    limit: int = Query(20, ge=1, le=200, description="Nombre de résultats"),
    enrich: bool = Query(False, description="Si true: scrape tous les résultats retournés qui ont un site web"),
):
    if not (where or (lat is not None and lon is not None)):
        raise HTTPException(
            status_code=422,
            detail="Paramètres requis: where=... OU lat=...&lon=...",
        )

    t0 = perf_counter()
    try:
        resp = ProspectController.search_prospects(
            where=where,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            radius_min_km=radius_min_km,
            category=category,
            tags=tags,
            limit=limit,
            enrich=enrich,
        )
        resp.setdefault("timings", {})
        resp["timings"]["total_seconds"] = round(perf_counter() - t0, 3)
        return resp

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")
