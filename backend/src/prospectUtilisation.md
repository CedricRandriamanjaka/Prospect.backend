# Prospects API — Quick Guide

## Endpoints
- GET `/health` → `{ "ok": true }`
- GET `/prospects` → recherche + (optionnel) enrichissement + tri/dedupe + stats

---

## GET /prospects — Paramètres

### 1) Localisation (obligatoire : 1 mode)
- Mode texte
  - `where` (str) ou `city` (str, ancien)
  - `radius_km` (float, optionnel) : **Note** : Si utilisé avec `where` sans `category` ni `tags`, ou avec `has`, le système utilise automatiquement un bbox au lieu d'un rayon pour éviter les timeouts.
- Mode carte
  - `lat` (float), `lon` (float)
  - `radius_km` (float, optionnel) : **Note** : Le rayon est automatiquement converti en zone rectangulaire (bbox) pour des raisons de performance. Les requêtes "around" sont désactivées car elles timeout facilement dans les zones denses. Le bbox couvre approximativement le rayon demandé.

### 1bis) Pagination par anneau (optionnel)
Permet de demander une zone entre 2 rayons (ex: commencer après 2 km).
- `radius_min_km` (float, optionnel)
  - Utilisé seulement si `radius_km` est fourni
  - Doit respecter : `0 <= radius_min_km < radius_km`
  - Si absent ou `0`, comportement standard (0 → radius_km)
  - Si > 0, la recherche se fait dans l'anneau : `(radius_min_km, radius_km]`
  - **Note** : Le filtrage de l'anneau est effectué côté client après récupération des résultats dans le bbox, pour des raisons de performance.

Exemples:
- Page 1 : `radius_min_km=0&radius_km=2`
- Page 2 : `radius_min_km=2&radius_km=4`
- Page 3 : `radius_min_km=4&radius_km=6`

---

### 2) Activité
- `tags` (str)  
  - Ex: `amenity=restaurant,tourism=hotel`
  - Ex: `restaurant,hotel`
  - Ex: `shop=beauty,shop=cosmetics,shop=perfumery` (pour cosmétiques)
  - **Tags OSM courants** : `amenity=*`, `shop=*`, `tourism=*`, `office=*`, `craft=*`, `leisure=*`, `healthcare=*`, `education=*`
- `category` (str, simple)  
  - Ex: `restaurant`, `hotel`, `spa`, `bakery`, `pharmacy`  
  - Utilisé seulement si `tags` est vide
  - **Note** : Les catégories disponibles sont limitées. Pour les cosmétiques, utiliser `tags=shop=beauty,shop=cosmetics,shop=perfumery` directement

### 3) Résultats
- `number` (int, défaut 20, 1..200) → nb final renvoyé
- **Limite** : Maximum 200 résultats par requête
- **Pour obtenir plus de résultats** : Utiliser la pagination par anneaux (voir section 1bis) ou faire plusieurs requêtes avec des zones différentes

### 4) Enrichissement (scraping)
- `enrich_max` (int, défaut 10, 0..200)
- `enrich_mode` (str, défaut `missing`)
  - `missing` : enrichit seulement si email+phone manquent
  - `always` : enrichit même si déjà des contacts
  - `never` : désactive

**Optimisation** : L'enrichissement est maintenant pré-sélectionné. Avant d'enrichir, le système :
1. Applique les filtres (`has`, `min_contacts`, `exclude_names`, `exclude_brands`)
2. Trie les résultats selon `sort`
3. Déduplique selon `dedupe`
4. Enrichit en priorité les meilleurs candidats (ceux qui survivront probablement aux filtres finaux)

Cela permet d'enrichir les prospects les plus pertinents en premier, réduisant le temps d'enrichissement et améliorant la qualité des résultats.

### 5) Filtres prospection
- `has` (csv) → `website,email,phone,whatsapp`
  - **Optimisation** : Si `has` est fourni, le filtre est appliqué directement dans la requête Overpass (pushdown), ce qui réduit le nombre de résultats récupérés et améliore les performances.
  - Ex: `has=website` → récupère uniquement les POI ayant un site web dans OSM
  - **Note** : Si `has` est utilisé avec `where` + `radius_km`, le système utilise automatiquement un bbox au lieu d'un rayon pour éviter les timeouts (les combinaisons de tags générées par `has` multiplient le nombre de requêtes Overpass).
- `min_contacts` (int, défaut 0, 0..4)
- `exclude_names` (csv) → exclure mots dans `nom`
- `exclude_brands` (csv) → exclure marque/opérateur

### 6) Tri / dédup / vue
- `sort` (défaut `contacts`) : `contacts|distance|name|random`
  - **`contacts`** : Tri par nombre de méthodes de contact (site web, email, téléphone, WhatsApp)
    - **Optimisation** : Les prospects avec un site web sont prioritaires comme tie-break (à nombre de contacts égal, ceux avec site remontent)
  - **`distance`** : Tri par distance (nécessite `lat`/`lon` ou `radius_km`)
  - **`name`** : Tri alphabétique par nom
  - **`random`** : Tri aléatoire (reproductible avec `seed`)
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
- Le `radius_km` est automatiquement converti en bbox approximatif pour éviter les timeouts
- Le bbox couvre la zone du rayon demandé

### 3bis) Anneau (commencer après 2 km)
`/prospects?lat=48.8566&lon=2.3522&radius_min_km=2&radius_km=4&category=hotel&sort=distance&number=30`
- Le bbox couvre le rayon maximum (`radius_km=4`)
- Le filtrage de l'anneau (`radius_min_km=2`) est effectué côté client après récupération

### 4) Uniquement contactables
`/prospects?where=Paris&category=spa&has=email,phone&min_contacts=1&number=50`

### 4bis) Pushdown has= (optimisé)
`/prospects?where=Maurice&category=hotel&has=website&min_contacts=1&number=30&enrich_max=5`
- Le filtre `has=website` est appliqué directement dans Overpass, réduisant le nombre de résultats récupérés
- L'enrichissement est plus rapide car on enrichit uniquement les prospects déjà contactables
- **Note** : Si `has` est utilisé avec `where` + `radius_km`, le système utilise automatiquement un bbox au lieu d'un rayon pour éviter les timeouts

### 5) Enrichissement (recommandé)
`/prospects?where=Paris&category=hotel&enrich_max=10&number=30`
- Les meilleurs candidats sont enrichis en priorité grâce à la pré-sélection

### 6) Vue légère export
`/prospects?where=Paris&category=bakery&view=light&number=100`

### 7) Random reproductible
`/prospects?where=Paris&category=restaurant&sort=random&seed=42&number=30`

### 8) Pagination par anneaux (séquence)
- Page 1 : `/prospects?where=Paris&radius_min_km=0&radius_km=2&category=restaurant&number=20`
- Page 2 : `/prospects?where=Paris&radius_min_km=2&radius_km=4&category=restaurant&number=20`
- Page 3 : `/prospects?where=Paris&radius_min_km=4&radius_km=6&category=restaurant&number=20`

### 9) Cas d'usage : Grandes quantités (300-10000+ résultats)
**Exemple : Trouver 1000 sociétés de cosmétiques à Maurice**

**Stratégie 1 : Pagination par anneaux**
- Faire plusieurs requêtes avec `radius_min_km` et `radius_km` croissants
- Chaque requête peut retourner jusqu'à 200 résultats
- Exemple pour 1000 résultats : 5 requêtes de 200 résultats chacune
  - Page 1 : `/prospects?where=Maurice&radius_min_km=0&radius_km=5&tags=shop=beauty,shop=cosmetics,shop=perfumery&number=200`
  - Page 2 : `/prospects?where=Maurice&radius_min_km=5&radius_km=10&tags=shop=beauty,shop=cosmetics,shop=perfumery&number=200`
  - Page 3 : `/prospects?where=Maurice&radius_min_km=10&radius_km=15&tags=shop=beauty,shop=cosmetics,shop=perfumery&number=200`
  - Page 4 : `/prospects?where=Maurice&radius_min_km=15&radius_km=20&tags=shop=beauty,shop=cosmetics,shop=perfumery&number=200`
  - Page 5 : `/prospects?where=Maurice&radius_min_km=20&radius_km=25&tags=shop=beauty,shop=cosmetics,shop=perfumery&number=200`

**Stratégie 2 : Zones géographiques différentes**
- Diviser le pays en régions/villes et faire une requête par zone
- Exemple : `/prospects?where=Port Louis&tags=shop=beauty,shop=cosmetics&number=200`
- Exemple : `/prospects?where=Curepipe&tags=shop=beauty,shop=cosmetics&number=200`

**Stratégie 3 : Combinaison tags**
- Utiliser plusieurs tags OSM pertinents pour maximiser les résultats
- Exemple : `/prospects?where=Maurice&tags=shop=beauty,shop=cosmetics,shop=perfumery,shop=pharmacy,amenity=pharmacy&number=200`
- Les pharmacies vendent souvent des cosmétiques

**Limitations importantes :**
- Maximum 200 résultats par requête (limite technique)
- La qualité des données OSM varie selon les régions (Maurice peut avoir moins de données que Paris)
- Pour 10000+ résultats, il faudra faire 50+ requêtes (automatisation recommandée)
- L'enrichissement (`enrich_max`) est limité à 200 par requête
