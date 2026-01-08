"""Controller pour gérer les prospects."""
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from src.prospect.open_street_map import get_prospects
from src.service.enrich import enrich_prospects
from src.service.postprocess import postprocess, category_to_tags
from src.db.crud import get_cache, set_cache, get_or_create_bbox, upsert_prospects


class ProspectController:
    """Controller pour la gestion des prospects."""
    
    @staticmethod
    def search_prospects(
        db: Session,
        where: Optional[str] = None,
        city: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius_km: Optional[float] = None,
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
        
        # Astuce: on récupère plus que number pour permettre filtrage/dedupe
        fetch_number = min(max(int(number) * 3, int(number)), 200)
        
        # Vérifier le cache DB (si city fourni)
        cache_key_city = (where or city or "").strip()
        if cache_key_city:
            cached = get_cache(db, cache_key_city, number)
            if cached:
                return cached
        
        # Récupérer depuis OSM
        try:
            results_raw, meta = get_prospects(
                where=where,
                city=city,
                lat=lat,
                lon=lon,
                radius_km=radius_km,
                tags=tags,
                number=fetch_number,
            )
        except ValueError as e:
            raise ValueError(str(e))
        except RuntimeError as e:
            raise RuntimeError(str(e))
        except Exception as e:
            raise Exception(f"Erreur interne: {e}")
        
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
            results_raw, enrich_meta = enrich_prospects(
                results_raw,
                max_enrich=enrich_max,
                return_meta=True,
                mode=mode,
            )
        
        # Point de référence pour distance
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
        
        # Sauvegarder en DB si city_key disponible
        city_key = None
        if cache_key_city:
            bbox_data = meta.get("bbox")
            if isinstance(bbox_data, list) and len(bbox_data) == 4:
                try:
                    city_bbox = get_or_create_bbox(db, cache_key_city, tuple(bbox_data))
                    city_key = city_bbox.city_key
                    
                    # Convertir les résultats pour la DB
                    db_prospects = []
                    for r in results_final:
                        # Extraire osm_type et osm_id depuis osm URL si possible
                        osm_url = r.get("osm", "")
                        osm_type = None
                        osm_id = None
                        if osm_url:
                            parts = osm_url.split("/")
                            if len(parts) >= 2:
                                osm_type = parts[-2] if parts[-2] in ["node", "way", "relation"] else "node"
                                try:
                                    osm_id = int(parts[-1])
                                except:
                                    pass
                        
                        if osm_type and osm_id:
                            db_prospects.append({
                                "osm_type": osm_type,
                                "osm_id": osm_id,
                                "name": r.get("nom"),
                                "activity_type": r.get("activite_type"),
                                "activity_value": r.get("activite_valeur"),
                                "website": r.get("site"),
                                "emails": r.get("emails", []),
                                "phones": r.get("telephones", []),
                                "stars": r.get("etoiles"),
                                "cuisine": r.get("cuisine"),
                                "opening_hours": r.get("horaires"),
                                "operator": r.get("operateur"),
                                "brand": r.get("marque"),
                                "address": r.get("adresse"),
                                "lat": r.get("lat"),
                                "lon": r.get("lon"),
                                "osm_url": osm_url,
                                "source": r.get("source", "OpenStreetMap"),
                            })
                    
                    if db_prospects:
                        upsert_prospects(db, db_prospects, city_key)
                except Exception:
                    pass  # Ignorer les erreurs DB pour ne pas casser l'API
        
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
        
        # Mettre en cache si city_key disponible
        if cache_key_city:
            try:
                set_cache(db, cache_key_city, number, {"params": meta}, resp)
            except Exception:
                pass  # Ignorer les erreurs de cache
        
        return resp
