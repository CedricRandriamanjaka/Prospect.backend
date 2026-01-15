// src/components/prospect/SearchForm.jsx
"use client"

import { useState, useRef, useEffect } from "react"
import {
  Box,
  Input,
  VStack,
  HStack,
  Text,
  Button,
  Badge,
  Card,
  Slider,
  Switch,
  NativeSelect,
} from "@chakra-ui/react"
import {
  FiSearch,
  FiMapPin,
  FiX,
  FiFilter,
} from "react-icons/fi"

// Liste de villes populaires pour l'autocomplétion
const POPULAR_CITIES = [
  "Paris, France",
  "Lyon, France",
  "Marseille, France",
  "Toulouse, France",
  "Nice, France",
  "Nantes, France",
  "Strasbourg, France",
  "Montpellier, France",
  "Bordeaux, France",
  "Lille, France",
  "London, UK",
  "New York, USA",
  "Los Angeles, USA",
  "Chicago, USA",
  "Toronto, Canada",
  "Vancouver, Canada",
  "Berlin, Germany",
  "Munich, Germany",
  "Madrid, Spain",
  "Barcelona, Spain",
  "Rome, Italy",
  "Milan, Italy",
  "Amsterdam, Netherlands",
  "Brussels, Belgium",
  "Vienna, Austria",
  "Zurich, Switzerland",
  "Stockholm, Sweden",
  "Copenhagen, Denmark",
  "Oslo, Norway",
  "Helsinki, Finland",
  "Dublin, Ireland",
  "Lisbon, Portugal",
  "Athens, Greece",
  "Warsaw, Poland",
  "Prague, Czech Republic",
  "Budapest, Hungary",
  "Bucharest, Romania",
  "Sofia, Bulgaria",
  "Belgrade, Serbia",
  "Zagreb, Croatia",
  "Tokyo, Japan",
  "Seoul, South Korea",
  "Singapore",
  "Hong Kong",
  "Sydney, Australia",
  "Melbourne, Australia",
  "Dubai, UAE",
  "Cairo, Egypt",
  "Johannesburg, South Africa",
  "São Paulo, Brazil",
  "Rio de Janeiro, Brazil",
  "Buenos Aires, Argentina",
  "Mexico City, Mexico",
  "Mumbai, India",
  "Delhi, India",
  "Bangalore, India",
  "Shanghai, China",
  "Beijing, China",
  "Bangkok, Thailand",
  "Manila, Philippines",
  "Jakarta, Indonesia",
  "Kuala Lumpur, Malaysia",
]

// Liste complète des catégories OSM avec libellés grand public
const OSM_CATEGORIES = [
  { value: "restaurant", label: "Restaurant" },
  { value: "cafe", label: "Café" },
  { value: "bar", label: "Bar" },
  { value: "fast_food", label: "Restauration rapide" },
  { value: "food_court", label: "Food court" },
  { value: "ice_cream", label: "Glacier" },
  { value: "hotel", label: "Hôtel" },
  { value: "hostel", label: "Auberge de jeunesse" },
  { value: "motel", label: "Motel" },
  { value: "guest_house", label: "Chambre d'hôtes" },
  { value: "apartment", label: "Appartement" },
  { value: "shop", label: "Magasin" },
  { value: "supermarket", label: "Supermarché" },
  { value: "bakery", label: "Boulangerie" },
  { value: "butcher", label: "Boucherie" },
  { value: "convenience", label: "Épicerie" },
  { value: "clothes", label: "Vêtements" },
  { value: "shoes", label: "Chaussures" },
  { value: "jewelry", label: "Bijouterie" },
  { value: "beauty", label: "Institut de beauté" },
  { value: "cosmetics", label: "Cosmétiques" },
  { value: "perfumery", label: "Parfumerie" },
  { value: "pharmacy", label: "Pharmacie" },
  { value: "fuel", label: "Station-service" },
  { value: "bank", label: "Banque" },
  { value: "atm", label: "Distributeur automatique" },
  { value: "post_office", label: "Bureau de poste" },
  { value: "hospital", label: "Hôpital" },
  { value: "clinic", label: "Clinique" },
  { value: "dentist", label: "Dentiste" },
  { value: "veterinary", label: "Vétérinaire" },
  { value: "school", label: "École" },
  { value: "university", label: "Université" },
  { value: "kindergarten", label: "Maternelle" },
  { value: "library", label: "Bibliothèque" },
  { value: "museum", label: "Musée" },
  { value: "theatre", label: "Théâtre" },
  { value: "cinema", label: "Cinéma" },
  { value: "parking", label: "Parking" },
  { value: "parking_entrance", label: "Entrée de parking" },
  { value: "gym", label: "Salle de sport" },
  { value: "fitness_centre", label: "Centre de fitness" },
  { value: "swimming_pool", label: "Piscine" },
  { value: "spa", label: "Spa" },
  { value: "beauty_salon", label: "Salon de beauté" },
  { value: "hairdresser", label: "Coiffeur" },
  { value: "nail_salon", label: "Institut de manucure" },
  { value: "tattoo", label: "Salon de tatouage" },
  { value: "car_rental", label: "Location de voiture" },
  { value: "car_repair", label: "Garage automobile" },
  { value: "car_wash", label: "Lavage auto" },
  { value: "bicycle_rental", label: "Location de vélo" },
  { value: "travel_agency", label: "Agence de voyage" },
  { value: "real_estate_agency", label: "Agence immobilière" },
  { value: "insurance", label: "Assurance" },
  { value: "lawyer", label: "Avocat" },
  { value: "accountant", label: "Expert-comptable" },
  { value: "notary", label: "Notaire" },
  { value: "funeral_directors", label: "Pompes funèbres" },
  { value: "florist", label: "Fleuriste" },
  { value: "gift", label: "Magasin de cadeaux" },
  { value: "toy", label: "Jouets" },
  { value: "book", label: "Librairie" },
  { value: "computer", label: "Informatique" },
  { value: "mobile_phone", label: "Téléphonie mobile" },
  { value: "electronics", label: "Électronique" },
  { value: "furniture", label: "Meubles" },
  { value: "hardware", label: "Quincaillerie" },
  { value: "paint", label: "Peinture" },
  { value: "garden_centre", label: "Jardinerie" },
  { value: "pet", label: "Animalerie" },
  { value: "optician", label: "Opticien" },
  { value: "massage", label: "Massage" },
  { value: "physiotherapist", label: "Kinésithérapeute" },
]


export default function SearchForm({
  onSearch,
  loading,
  onRadiusChange,
  initialWhere = "",
  initialRadius = 5,
  initialRadiusMin = 0,
  initialCategories = [],
  initialLimit = 20,
  initialEnrich = false,
}) {
  const [where, setWhere] = useState(initialWhere)
  const [useRadius, setUseRadius] = useState(initialRadius > 0)
  const [radius, setRadius] = useState(Math.max(0, Math.min(initialRadius || 5, 50)))
  const [radiusMin, setRadiusMin] = useState(Math.max(0, Math.min(initialRadiusMin, Math.max(0, (initialRadius || 5) - 0.5))))
  const [categories, setCategories] = useState(initialCategories)
  const [limit, setLimit] = useState(initialLimit)
  const [enrich, setEnrich] = useState(initialEnrich)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [filteredCities, setFilteredCities] = useState([])
  const [categorySearch, setCategorySearch] = useState("")
  const inputRef = useRef(null)
  const suggestionsRef = useRef(null)

  // S'assurer que radiusMin est toujours < radius
  useEffect(() => {
    if (useRadius && radiusMin >= radius && radius > 0) {
      const adjustedMin = Math.max(0, radius - 0.5)
      setRadiusMin(adjustedMin)
      onRadiusChange?.(radius, adjustedMin)
    }
  }, [radius, radiusMin, useRadius, onRadiusChange])

  // Filtrer les villes selon la saisie
  useEffect(() => {
    if (!where || where.length < 2) {
      setFilteredCities([])
      setShowSuggestions(false)
      return
    }

    const filtered = POPULAR_CITIES.filter((city) =>
      city.toLowerCase().includes(where.toLowerCase())
    ).slice(0, 8)
    setFilteredCities(filtered)
    setShowSuggestions(filtered.length > 0)
  }, [where])

  // Fermer les suggestions en cliquant à l'extérieur
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target) &&
        inputRef.current &&
        !inputRef.current.contains(event.target)
      ) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleCitySelect = (city) => {
    setWhere(city)
    setShowSuggestions(false)
  }

  const handleRemoveCategory = (catToRemove) => {
    setCategories(categories.filter((c) => c !== catToRemove))
  }

  const handleAddCategory = (category) => {
    if (!categories.includes(category)) {
      setCategories([...categories, category])
    }
  }

  const handleSearch = () => {
    const params = new URLSearchParams()

    if (where) params.append("where", where)
    
    // Ajouter le rayon seulement si activé
    if (useRadius && radius > 0) {
      params.append("radius_km", radius.toString())
      if (radiusMin > 0) {
        params.append("radius_min_km", radiusMin.toString())
      }
    }
    
    // Les catégories sont converties en tags OSM par le backend
    if (categories.length > 0) params.append("category", categories.join(","))
    
    // Nombre de résultats
    if (limit && limit > 0) {
      params.append("limit", Math.min(200, Math.max(1, limit)).toString())
    }
    
    // Enrichissement
    if (enrich) {
      params.append("enrich", "true")
    }

    onSearch(params.toString())
  }

  const hasFilters = where || categories.length > 0

  // Filtrer les catégories selon la recherche
  const filteredCategories = OSM_CATEGORIES.filter((cat) =>
    cat.label.toLowerCase().includes(categorySearch.toLowerCase()) ||
    cat.value.toLowerCase().includes(categorySearch.toLowerCase())
  )


  return (
    <Card.Root
      shadow="lg"
      borderWidth="1px"
      borderColor="border.subtle"
      bg="surface"
      _dark={{ bg: "surface", borderColor: "border" }}
    >
      <Card.Body p="6">
        <VStack gap="5" align="stretch">
          {/* Header */}
          <VStack align="start" gap="1">
            <Text fontSize="2xl" fontWeight="800" bgGradient="to-r" bgClip="text" color="blue.600" _dark={{ color: "blue.400" }}>
              Recherche de Prospects
            </Text>
            <Text fontSize="sm" color="fg.muted">
              Trouvez des entreprises et commerces dans le monde entier
            </Text>
          </VStack>

          {/* Recherche principale - Localisation */}
          <Box position="relative">
            <Box position="relative">
              <Input
                ref={inputRef}
                placeholder="Où chercher ? (ville, pays, adresse...)"
                value={where}
                onChange={(e) => setWhere(e.target.value)}
                onFocus={() => where.length >= 2 && setShowSuggestions(true)}
                size="lg"
                fontSize="md"
                pl="12"
                borderColor="border"
                _focus={{ borderColor: "blue.500", boxShadow: "0 0 0 1px var(--chakra-colors-blue-500)" }}
              />
              <Box
                position="absolute"
                left="4"
                top="50%"
                transform="translateY(-50%)"
                color="fg.muted"
                pointerEvents="none"
                zIndex="1"
              >
                <FiMapPin size="20" />
              </Box>
            </Box>

            {/* Suggestions de villes */}
            {showSuggestions && filteredCities.length > 0 && (
              <Box
                ref={suggestionsRef}
                position="absolute"
                top="100%"
                left="0"
                right="0"
                mt="1"
                bg="surface"
                borderWidth="1px"
                borderColor="border"
                rounded="md"
                shadow="xl"
                zIndex="1000"
                maxH="300px"
                overflowY="auto"
                _dark={{ bg: "surface", borderColor: "border" }}
              >
                {filteredCities.map((city, idx) => (
                  <Box
                    key={idx}
                    px="4"
                    py="3"
                    cursor="pointer"
                    _hover={{ bg: "bg.subtle" }}
                    onClick={() => handleCitySelect(city)}
                    borderBottomWidth={idx < filteredCities.length - 1 ? "1px" : "0"}
                    borderColor="border.subtle"
                  >
                    <HStack gap="2">
                      <FiMapPin size="16" color="var(--chakra-colors-blue-500)" />
                      <Text fontSize="sm">{city}</Text>
                    </HStack>
                  </Box>
                ))}
              </Box>
            )}
          </Box>

          {/* Rayon de recherche - Optionnel */}
          <VStack gap="3" align="stretch" p="4" bg="bg.subtle" rounded="lg" borderWidth="1px" borderColor="border.subtle">
            <HStack justify="space-between" align="center">
              <HStack gap="2">
                <FiFilter size="18" color="var(--chakra-colors-blue-500)" />
                <VStack align="start" gap="0">
                  <Text fontWeight="600" fontSize="sm">
                    Limiter la zone de recherche
                  </Text>
                  <Text fontSize="xs" color="fg.muted">
                    Définir un périmètre autour de votre localisation (optionnel)
                  </Text>
                </VStack>
              </HStack>
              <Switch.Root
                checked={useRadius}
                onCheckedChange={(details) => {
                  const newUseRadius = details.checked
                  setUseRadius(newUseRadius)
                  if (!newUseRadius) {
                    setRadius(0)
                    setRadiusMin(0)
                    onRadiusChange?.(0, 0)
                  } else {
                    const defaultRadius = 5
                    setRadius(defaultRadius)
                    setRadiusMin(0)
                    onRadiusChange?.(defaultRadius, 0)
                  }
                }}
              >
                <Switch.HiddenInput />
                <Switch.Control>
                  <Switch.Thumb />
                </Switch.Control>
              </Switch.Root>
            </HStack>

            {useRadius && (
              <VStack gap="3" align="stretch">
                {radiusMin > 0 && radius > radiusMin && (
                  <Box>
                    <HStack justify="space-between" mb="2">
                      <Text fontSize="xs" color="fg.muted">
                        Distance minimum
                      </Text>
                      <Text fontSize="xs" fontWeight="600">
                        {radiusMin} km
                      </Text>
                    </HStack>
                    <Slider.Root
                      value={[Math.max(0, Math.min(radiusMin, radius - 0.5))]}
                      onValueChange={(details) => {
                        const value = Array.isArray(details.value) ? details.value[0] : details.value
                        const newMin = Math.max(0, Math.min(value, radius - 0.5))
                        setRadiusMin(newMin)
                        onRadiusChange?.(radius, newMin)
                      }}
                      min={0}
                      max={Math.max(0.5, radius - 0.5)}
                      step={0.5}
                      size="sm"
                      colorPalette="gray"
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Range />
                        </Slider.Track>
                        <Slider.Thumb index={0}>
                          <Slider.HiddenInput />
                        </Slider.Thumb>
                      </Slider.Control>
                    </Slider.Root>
                  </Box>
                )}

                <Box>
                  <HStack justify="space-between" mb="2">
                    <Text fontSize="xs" color="fg.muted">
                      Distance maximum
                    </Text>
                    <Text fontSize="xs" fontWeight="600">
                      {radius} km
                    </Text>
                  </HStack>
                  <Slider.Root
                    value={[Math.max(0.5, Math.min(radius, 50))]}
                    onValueChange={(details) => {
                      const value = Array.isArray(details.value) ? details.value[0] : details.value
                      const newRadius = Math.max(0.5, Math.min(value, 50))
                      setRadius(newRadius)
                      if (radiusMin >= newRadius) {
                        const adjustedMin = Math.max(0, newRadius - 0.5)
                        setRadiusMin(adjustedMin)
                        onRadiusChange?.(newRadius, adjustedMin)
                      } else {
                        onRadiusChange?.(newRadius, radiusMin)
                      }
                    }}
                    min={0.5}
                    max={50}
                    step={0.5}
                    size="sm"
                    colorPalette="blue"
                  >
                    <Slider.Control>
                      <Slider.Track>
                        <Slider.Range />
                      </Slider.Track>
                      <Slider.Thumb index={0}>
                        <Slider.HiddenInput />
                      </Slider.Thumb>
                    </Slider.Control>
                  </Slider.Root>
                </Box>

                <HStack gap="2">
                  <Button
                    size="xs"
                    variant="ghost"
                    onClick={() => {
                      setRadiusMin(0)
                      setRadius(5)
                      onRadiusChange?.(5, 0)
                    }}
                  >
                    <FiX size="12" />
                    Réinitialiser
                  </Button>
                  {radiusMin === 0 && radius > 0.5 && (
                    <Button
                      size="xs"
                      variant="outline"
                      onClick={() => {
                        const newMin = Math.min(1, radius - 0.5)
                        setRadiusMin(newMin)
                        onRadiusChange?.(radius, newMin)
                      }}
                    >
                      Ajouter distance minimum
                    </Button>
                  )}
                </HStack>
              </VStack>
            )}
          </VStack>

          {/* Nombre de résultats */}
          <VStack gap="2" align="stretch" p="4" bg="bg.subtle" rounded="lg" borderWidth="1px" borderColor="border.subtle">
            <VStack align="start" gap="1">
              <Text fontWeight="600" fontSize="sm">
                Nombre de résultats
              </Text>
              <Text fontSize="xs" color="fg.muted">
                Choisissez combien de prospects vous souhaitez obtenir (maximum 200)
              </Text>
            </VStack>
            <HStack gap="3" align="center">
              <Slider.Root
                value={[Math.max(1, Math.min(limit, 200))]}
                onValueChange={(details) => {
                  const value = Array.isArray(details.value) ? details.value[0] : details.value
                  setLimit(Math.max(1, Math.min(value, 200)))
                }}
                min={1}
                max={200}
                step={1}
                size="sm"
                colorPalette="blue"
                flex="1"
              >
                <Slider.Control>
                  <Slider.Track>
                    <Slider.Range />
                  </Slider.Track>
                  <Slider.Thumb index={0}>
                    <Slider.HiddenInput />
                  </Slider.Thumb>
                </Slider.Control>
              </Slider.Root>
              <Box minW="60px" textAlign="center">
                <Text fontSize="sm" fontWeight="700">
                  {limit}
                </Text>
              </Box>
            </HStack>
          </VStack>

          {/* Enrichissement */}
          <VStack gap="2" align="stretch" p="4" bg="bg.subtle" rounded="lg" borderWidth="1px" borderColor="border.subtle">
            <HStack justify="space-between" align="start">
              <VStack align="start" gap="1" flex="1">
                <Text fontWeight="600" fontSize="sm">
                  Enrichissement des données
                </Text>
                <Text fontSize="xs" color="fg.muted">
                  Recherche automatique d'informations supplémentaires (emails, téléphones) sur les sites web des entreprises.
                  <Box as="span" fontWeight="600" color="orange.600" _dark={{ color: "orange.400" }} display="block" mt="1">
                    ⚠️ Augmente significativement le temps d'exécution
                  </Box>
                </Text>
              </VStack>
              <Switch.Root
                checked={enrich}
                onCheckedChange={(details) => setEnrich(details.checked)}
              >
                <Switch.HiddenInput />
                <Switch.Control>
                  <Switch.Thumb />
                </Switch.Control>
              </Switch.Root>
            </HStack>
          </VStack>

          {/* Types d'établissements (Catégories) */}
          <VStack gap="3" align="stretch">
            <VStack align="start" gap="1">
              <Text fontWeight="600" fontSize="sm">
                Types d'établissements
              </Text>
              <Text fontSize="xs" color="fg.muted">
                Sélectionnez les types de commerces ou services que vous recherchez
              </Text>
            </VStack>

            {categories.length > 0 && (
              <HStack gap="2" flexWrap="wrap">
                {categories.map((cat) => {
                  const catInfo = OSM_CATEGORIES.find((c) => c.value === cat)
                  return (
                    <Badge
                      key={cat}
                      colorPalette="purple"
                      variant="solid"
                      px="2"
                      py="1"
                      fontSize="xs"
                      cursor="pointer"
                      onClick={() => handleRemoveCategory(cat)}
                      _hover={{ opacity: 0.8 }}
                    >
                      {catInfo?.label || cat}
                      <Box as="span" ml="1">×</Box>
                    </Badge>
                  )
                })}
              </HStack>
            )}

            <Box>
              <Input
                placeholder="Rechercher un type d'établissement..."
                value={categorySearch}
                onChange={(e) => setCategorySearch(e.target.value)}
                size="sm"
                mb="2"
              />
              <Box
                maxH="200px"
                overflowY="auto"
                borderWidth="1px"
                borderColor="border"
                rounded="md"
                p="2"
                bg="bg.subtle"
              >
                <VStack align="stretch" gap="1">
                  {filteredCategories.slice(0, 20).map((cat) => (
                    <Box
                      key={cat.value}
                      px="3"
                      py="2"
                      cursor="pointer"
                      rounded="sm"
                      _hover={{ bg: "bg.emphasized" }}
                      onClick={() => {
                        handleAddCategory(cat.value)
                        setCategorySearch("")
                      }}
                      display={categories.includes(cat.value) ? "none" : "block"}
                    >
                      <Text fontSize="sm">{cat.label}</Text>
                    </Box>
                  ))}
                  {filteredCategories.length === 0 && (
                    <Text fontSize="xs" color="fg.muted" px="3" py="2">
                      Aucun résultat
                    </Text>
                  )}
                </VStack>
              </Box>
            </Box>
          </VStack>

          {/* Bouton de recherche */}
          <Button
            size="lg"
            colorPalette="blue"
            onClick={handleSearch}
            loading={loading}
            disabled={!hasFilters && loading}
            w="100%"
            h="50px"
            fontSize="md"
            fontWeight="700"
            shadow="md"
            _hover={{ shadow: "lg", transform: "translateY(-1px)" }}
            transition="all 0.2s"
          >
            <FiSearch size="20" />
            <Box as="span" ml="2">
              {loading ? "Recherche en cours..." : "Lancer la recherche"}
            </Box>
          </Button>
        </VStack>
      </Card.Body>
    </Card.Root>
  )
}
