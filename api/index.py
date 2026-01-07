from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from prospect.osm import get_prospects
from prospect.enrich import enrich_prospects

app = FastAPI(title="Prospect.com API", version="0.1")

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
    city: str = Query(..., min_length=2),
    number: int = Query(20, ge=1),
    enrich: bool = Query(False),
    enrich_max: int = Query(10, ge=0),
):
    results = get_prospects(city, number)

    # scraping seulement si demandé
    if enrich and enrich_max > 0:
        results = enrich_prospects(results, max_enrich=enrich_max)

    return {
        "city": city,
        "count": number,
        "enrich": enrich,
        "enrich_max": enrich_max,
        "results": results,
    }
