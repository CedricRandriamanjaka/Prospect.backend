import re

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    # Ne pas remplacer _ par espace pour préserver les noms avec underscore
    s = re.sub(r"[\s\-]+", " ", s)
    return s.strip()

def category_to_tags(category: str) -> str:
    """
    Retourne une string 'tags' compatible avec notre provider.
    - mapping pour les cas courants
    - sinon fallback: "valeur seule" => ex: "restaurant"
    """
    c = _norm(category)

    mapping = {
        # Restauration
        "restaurant": "amenity=restaurant",
        "restau": "amenity=restaurant",
        "cafe": "amenity=cafe",
        "bar": "amenity=bar",
        "fast_food": "amenity=fast_food",
        "food_court": "amenity=food_court",
        "ice_cream": "amenity=ice_cream",
        
        # Hébergement
        "hotel": "tourism=hotel",
        "hostel": "tourism=hostel",
        "motel": "tourism=motel",
        "guest_house": "tourism=guest_house",
        "apartment": "tourism=apartment",
        
        # Commerce (générique - cherche tous les shops)
        # Note: "shop" seul cherche tous les types de shops via DEFAULT_POI_KEYS
        "supermarket": "shop=supermarket",
        "bakery": "shop=bakery",
        "boulangerie": "shop=bakery",
        "butcher": "shop=butcher",
        "convenience": "shop=convenience",
        "clothes": "shop=clothes",
        "shoes": "shop=shoes",
        "jewelry": "shop=jewelry",
        "beauty": "shop=beauty",
        "cosmetics": "shop=cosmetics",
        "perfumery": "shop=perfumery",
        "pharmacy": "amenity=pharmacy",
        "pharmacie": "amenity=pharmacy",
        "fuel": "amenity=fuel",
        "bank": "amenity=bank",
        "atm": "amenity=atm",
        "post_office": "amenity=post_office",
        
        # Santé
        "hospital": "amenity=hospital",
        "clinic": "amenity=clinic",
        "dentist": "amenity=dentist",
        "veterinary": "amenity=veterinary",
        "veterinaire": "amenity=veterinary",
        
        # Éducation
        "school": "amenity=school",
        "university": "amenity=university",
        "kindergarten": "amenity=kindergarten",
        "library": "amenity=library",
        
        # Culture & Loisirs
        "museum": "tourism=museum",
        "theatre": "amenity=theatre",
        "cinema": "amenity=cinema",
        "parking": "amenity=parking",
        "parking_entrance": "amenity=parking_entrance",
        "gym": "leisure=fitness_centre",
        "fitness": "leisure=fitness_centre",
        "fitness_centre": "leisure=fitness_centre",
        "swimming_pool": "leisure=swimming_pool",
        # Spa : shop=beauty (beauty=spa est un sous-tag, cherché via shop=beauty) OU amenity=public_bath (bains publics/thermaux)
        # Note: beauty=spa ne peut pas être recherché directement via Overpass, on cherche shop=beauty
        "spa": "shop=beauty,amenity=public_bath",
        "beauty_salon": "shop=beauty",
        "hairdresser": "shop=hairdresser",
        "nail_salon": "shop=beauty",
        "tattoo": "shop=tattoo",
        "massage": "shop=massage",
        "physiotherapist": "healthcare=physiotherapist",
        
        # Transport
        "car_rental": "amenity=car_rental",
        "car_repair": "amenity=car_repair,shop=car_repair",
        "car_wash": "amenity=car_wash",
        "bicycle_rental": "amenity=bicycle_rental",
        "travel_agency": "shop=travel_agency,office=travel_agent",
        "real_estate_agency": "office=estate_agent",
        
        # Services professionnels
        "insurance": "office=insurance",
        "lawyer": "office=lawyer",
        "accountant": "office=accountant",
        "notary": "office=notary",
        "funeral_directors": "shop=funeral_directors",
        
        # Autres commerces
        "florist": "shop=florist",
        "gift": "shop=gift",
        "toy": "shop=toy",
        "book": "shop=book",
        "computer": "shop=computer",
        "mobile_phone": "shop=mobile_phone",
        "electronics": "shop=electronics",
        "furniture": "shop=furniture",
        "hardware": "shop=hardware",
        "paint": "shop=paint",
        "garden_centre": "shop=garden_centre",
        "pet": "shop=pet",
        "optician": "shop=optician",
    }

    # si user te donne déjà du tags (key=value,...), on le laisse passer
    if "=" in c or "," in c:
        return category.strip()

    return mapping.get(c, category.strip())
