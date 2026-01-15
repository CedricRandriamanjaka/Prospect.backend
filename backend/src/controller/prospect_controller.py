from typing import Optional, Dict, Any

from src.prospect.open_street_map.osm import get_prospects
from src.service.enrich import enrich_prospects
from src.service.tags import category_to_tags  # petit helper


class ProspectController:
    @staticmethod
    def search_prospects(
        *,
        where: Optional[str],
        lat: Optional[float],
        lon: Optional[float],
        radius_km: Optional[float],
        radius_min_km: Optional[float],
        category: Optional[str],
        tags: Optional[str],
        limit: int,
        enrich: bool,
    ) -> Dict[str, Any]:
        # category -> tags si tags non fourni
        if (not tags or not tags.strip()) and category and category.strip():
            tags = category_to_tags(category)

        results, meta = get_prospects(
            where=where,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            radius_min_km=radius_min_km,
            tags=tags,
            limit=limit,
        )

        enrich_meta = {"enabled": bool(enrich), "enriched_count": 0, "total_seconds": 0.0, "avg_seconds": 0.0}
        if enrich:
            results, enrich_meta = enrich_prospects(results, return_meta=True)

        return {
            "query": meta,
            "count": len(results),
            "enrich": enrich,
            "timings": {
                "provider": meta.get("timings", {}),
                "enrichment": enrich_meta,
            },
            "results": results,
        }
