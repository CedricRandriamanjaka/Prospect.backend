"""Routes FastAPI pour l'API."""
from time import perf_counter
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from src.db import db_session
from src.controller.prospect_controller import ProspectController

router = APIRouter()


@router.get("/health")
def health():
    """Endpoint de santé."""
    return {"ok": True}


@router.get("/prospects")
def prospects(
    db: Session = Depends(db_session),
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
    """Recherche de prospects."""
    if not (where or city or (lat is not None and lon is not None)):
        raise HTTPException(
            status_code=422,
            detail="Paramètres requis: where=... OU lat=...&lon=... (city accepté aussi).",
        )

    t_total0 = perf_counter()

    try:
        result = ProspectController.search_prospects(
            db=db,
            where=where,
            city=city,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            tags=tags,
            category=category,
            number=number,
            enrich_max=enrich_max,
            enrich_mode=enrich_mode,
            has=has,
            min_contacts=min_contacts,
            exclude_names=exclude_names,
            exclude_brands=exclude_brands,
            sort=sort,
            dedupe=dedupe,
            view=view,
            seed=seed,
            include_coverage=include_coverage,
        )
        
        total_seconds = perf_counter() - t_total0
        result["timings"]["total_seconds"] = round(total_seconds, 3)
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")
