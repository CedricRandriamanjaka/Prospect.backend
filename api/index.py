from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from prospect.osm import get_prospects

app = FastAPI(title="Prospect.com API", version="0.1")

# CORS pour Netlify (mettre ton domaine Netlify plus tard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod: ["https://ton-site.netlify.app"]
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
):
    return {
        "city": city,
        "count": number,
        "results": get_prospects(city, number),
    }
