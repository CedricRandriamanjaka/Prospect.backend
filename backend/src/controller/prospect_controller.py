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
        # Gère plusieurs catégories séparées par des virgules
        if (not tags or not tags.strip()) and category and category.strip():
            # Si plusieurs catégories, les mapper séparément puis les joindre
            categories = [c.strip() for c in category.split(",") if c.strip()]
            if categories:
                mapped_tags = []
                for cat in categories:
                    mapped = category_to_tags(cat)
                    # Si le mapping retourne plusieurs tags (séparés par virgule), les ajouter individuellement
                    if "," in mapped:
                        mapped_tags.extend([t.strip() for t in mapped.split(",") if t.strip()])
                    else:
                        mapped_tags.append(mapped)
                tags = ",".join(mapped_tags)

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
