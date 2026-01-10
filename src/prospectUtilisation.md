# Prospects API — Quick Guide

## Endpoints
- GET `/health` → `{ "ok": true }`
- GET `/prospects` → recherche + (optionnel) enrichissement + tri/dedupe + stats

---

## GET /prospects — Paramètres

### 1) Localisation (obligatoire : 1 mode)
- Mode texte
  - `where` (str) ou `city` (str, ancien)
- Mode carte
  - `lat` (float), `lon` (float)
  - `radius_km` (float, optionnel)

### 1bis) Pagination par anneau (optionnel)
Permet de demander une zone entre 2 rayons (ex: commencer après 2 km).
- `radius_min_km` (float, optionnel)
  - Utilisé seulement si `radius_km` est fourni
  - Doit respecter : `0 <= radius_min_km < radius_km`
  - Si absent ou `0`, comportement standard (0 → radius_km)
  - Si > 0, la recherche se fait dans l’anneau : `(radius_min_km, radius_km]`

Exemples:
- Page 1 : `radius_min_km=0&radius_km=2`
- Page 2 : `radius_min_km=2&radius_km=4`
- Page 3 : `radius_min_km=4&radius_km=6`

---

### 2) Activité
- `tags` (str)  
  - Ex: `amenity=restaurant,tourism=hotel`
  - Ex: `restaurant,hotel`
- `category` (str, simple)  
  - Ex: `restaurant`, `hotel`, `spa`, `bakery`  
  - Utilisé seulement si `tags` est vide

### 3) Résultats
- `number` (int, défaut 20, 1..200) → nb final renvoyé

### 4) Enrichissement (scraping)
- `enrich_max` (int, défaut 10, 0..200)
- `enrich_mode` (str, défaut `missing`)
  - `missing` : enrichit seulement si email+phone manquent
  - `always` : enrichit même si déjà des contacts
  - `never` : désactive

### 5) Filtres prospection
- `has` (csv) → `website,email,phone,whatsapp`
- `min_contacts` (int, défaut 0, 0..4)
- `exclude_names` (csv) → exclure mots dans `nom`
- `exclude_brands` (csv) → exclure marque/opérateur

### 6) Tri / dédup / vue
- `sort` (défaut `contacts`) : `contacts|distance|name|random`
- `dedupe` (défaut `smart`) : `none|strict|smart`
- `seed` (int) : pour `sort=random`
- `view` (défaut `full`) : `full|light`

### 7) Stats
- `include_coverage` (bool, défaut true)

---

## Réponse (résumé)
- `results` : liste prospects
- `timings` : `total_seconds`, `osm_seconds`, `enrichment_seconds`, `postprocess_seconds`
- `coverage` : % avec site/email/phone/whatsapp (si activé)
- En `view=full`, chaque item contient `sales` et (si enrich) `enrich_details`

---

## Exemples

### 1) Simple
`/prospects?where=Paris&category=restaurant&number=20`

### 2) Tags précis (plus rapide)
`/prospects?where=Paris&tags=amenity=restaurant,tourism=hotel&number=30`

### 3) Clic carte + distance
`/prospects?lat=48.8566&lon=2.3522&radius_km=2&category=hotel&sort=distance&number=30`

### 3bis) Anneau (commencer après 2 km)
`/prospects?lat=48.8566&lon=2.3522&radius_min_km=2&radius_km=4&category=hotel&sort=distance&number=30`

### 4) Uniquement contactables
`/prospects?where=Paris&category=spa&has=email,phone&min_contacts=1&number=50`

### 5) Enrichissement (recommandé)
`/prospects?where=Paris&category=hotel&enrich_mode=missing&enrich_max=10&number=30`

### 6) Vue légère export
`/prospects?where=Paris&category=bakery&view=light&number=100`

### 7) Random reproductible
`/prospects?where=Paris&category=restaurant&sort=random&seed=42&number=30`

### 8) Pagination par anneaux (séquence)
- Page 1 : `/prospects?where=Paris&radius_min_km=0&radius_km=2&category=restaurant&number=20`
- Page 2 : `/prospects?where=Paris&radius_min_km=2&radius_km=4&category=restaurant&number=20`
- Page 3 : `/prospects?where=Paris&radius_min_km=4&radius_km=6&category=restaurant&number=20`
