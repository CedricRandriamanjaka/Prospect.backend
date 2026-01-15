import re

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[\s\-_]+", " ", s)
    return s.strip()

def category_to_tags(category: str) -> str:
    """
    Retourne une string 'tags' compatible avec notre provider.
    - mapping pour les cas courants
    - sinon fallback: "valeur seule" => ex: "restaurant"
    """
    c = _norm(category)

    mapping = {
        "restaurant": "amenity=restaurant",
        "restau": "amenity=restaurant",
        "spa": "leisure=spa,amenity=spa",
        "hotel": "tourism=hotel",
        "bakery": "shop=bakery",
        "boulangerie": "shop=bakery",
        "pharmacy": "amenity=pharmacy",
        "pharmacie": "amenity=pharmacy",
        "bar": "amenity=bar",
        "cafe": "amenity=cafe",
        "gym": "leisure=fitness_centre",
        "fitness": "leisure=fitness_centre",
        "supermarket": "shop=supermarket",
    }

    # si user te donne déjà du tags (key=value,...), on le laisse passer
    if "=" in c or "," in c:
        return category.strip()

    return mapping.get(c, category.strip())
