"""Controller pour gérer les prospects."""
from typing import Optional, Dict, Any
from src.prospect.open_street_map import get_prospects
from src.service.enrich import enrich_prospects
from src.service.postprocess import (
    postprocess,
    category_to_tags,
    add_sales_fields,
    filter_results,
    sort_results,
    dedupe_results,
)


class ProspectController:
    """Controller pour la gestion des prospects."""
    
    @staticmethod
    def search_prospects(
        where: Optional[str] = None,
        city: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius_km: Optional[float] = None,
        radius_min_km: Optional[float] = None,   # ✅ AJOUT
        tags: Optional[str] = None,
        category: Optional[str] = None,
        number: int = 20,
        enrich_max: int = 10,
        enrich_mode: str = "missing",
        has: Optional[str] = None,
        min_contacts: int = 0,
        exclude_names: Optional[str] = None,
        exclude_brands: Optional[str] = None,
        sort: str = "contacts",
        dedupe: str = "smart",
        view: str = "full",
        seed: Optional[int] = None,
        include_coverage: bool = True,
    ) -> Dict[str, Any]:
        """
        Recherche et retourne des prospects selon les critères.
        
        Returns:
            Dictionnaire avec les résultats et métadonnées
        """
        # category -> tags (si tags non fourni)
        if (not tags or not tags.strip()) and category:
            mapped = category_to_tags(category)
            if mapped:
                tags = mapped

        def _csv(s: Optional[str]) -> list[str]:
            if not s:
                return []
            return [x.strip() for x in s.split(",") if x.strip()]

        has_list = _csv(has)
        ex_names = [x.lower() for x in _csv(exclude_names)]
        ex_brands = [x.lower() for x in _csv(exclude_brands)]

        # Astuce: on récupère plus que number pour permettre filtrage/dedupe
        fetch_number = min(max(int(number) * 3, int(number)), 200)

        # Récupérer depuis OSM
        try:
            results_raw, meta = get_prospects(
                where=where,
                city=city,
                lat=lat,
                lon=lon,
                radius_km=radius_km,
                radius_min_km=radius_min_km,  # ✅ AJOUT
                tags=tags,
                number=fetch_number,
                osm_has=has_list,  # ✅ pushdown "has" côté OSM (amélioration #2)
            )
        except ValueError as e:
            raise ValueError(str(e))
        except RuntimeError as e:
            raise RuntimeError(str(e))
        except Exception as e:
            raise Exception(f"Erreur interne: {e}")

        # Point de référence pour distance (calculé AVANT enrich pour aider la pré-sélection)
        ref_point = None
        try:
            if lat is not None and lon is not None:
                ref_point = (float(lat), float(lon))
            else:
                bbox = meta.get("bbox")
                if isinstance(bbox, list) and len(bbox) == 4:
                    s, w, n, e = map(float, bbox)
                    ref_point = ((s + n) / 2.0, (w + e) / 2.0)
                else:
                    ml = meta.get("lat")
                    mn = meta.get("lon")
                    if isinstance(ml, (int, float)) and isinstance(mn, (int, float)):
                        ref_point = (float(ml), float(mn))
        except Exception:
            ref_point = None

        # Enrichissement
        enrich_meta = {
            "enriched_count": 0,
            "total_seconds": 0.0,
            "avg_seconds": 0.0,
            "max_enrich": enrich_max,
            "mode": enrich_mode,
        }

        if enrich_max > 0 and (enrich_mode or "").lower() != "never":
            mode = (enrich_mode or "missing").lower()

            # ✅ Amélioration #1: pré-sélection des meilleurs candidats AVANT enrichissement
            # On enrichit en priorité ce qui survivra probablement aux filtres/tri/dédup.
            try:
                # dériver sales + appliquer filtres business
                stage = list(results_raw)
                add_sales_fields(stage, ref_point=ref_point)
                filtered = filter_results(
                    stage,
                    has=has_list,
                    min_contacts=min_contacts,
                    exclude_names=ex_names,
                    exclude_brands=ex_brands,
                )
                sorted_stage = sort_results(filtered, sort=sort, seed=seed)
                deduped_stage, _ = dedupe_results(sorted_stage, mode=dedupe)

                # pool de candidats (on ne prend pas que 30, pour garder de la marge)
                top_k = max(int(number) * 2, int(enrich_max) * 3, int(enrich_max))
                top_k = min(top_k, len(deduped_stage))

                # reorder: meilleurs d'abord => enrich_prospects enrichira les bons en premier
                key = lambda r: (r.get("entity_key") or r.get("osm") or "").strip()
                picked = deduped_stage[:top_k]
                picked_keys = set([key(r) for r in picked if key(r)])

                prioritized = picked + [r for r in results_raw if key(r) not in picked_keys]
                results_raw, enrich_meta = enrich_prospects(
                    prioritized,
                    max_enrich=enrich_max,
                    return_meta=True,
                    mode=mode,
                )
            except Exception:
                # fallback: ancien comportement (ne jamais casser la prod)
                results_raw, enrich_meta = enrich_prospects(
                    results_raw,
                    max_enrich=enrich_max,
                    return_meta=True,
                    mode=mode,
                )
        
        # Post-process: filtres / tri / dedupe / view
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
        
        # Construire la réponse
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
                "enrichment": enrich_meta,
            },
            "results": results_final,
        }
        
        if include_coverage:
            resp["coverage"] = coverage
        
        return resp
