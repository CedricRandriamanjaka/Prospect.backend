"use client"

import { useState, useCallback, useRef } from "react"
import {
  Box,
  Button,
  Container,
  Heading,
  VStack,
  HStack,
  Text,
  Input,
  Badge,
  SimpleGrid,
  Card,
  IconButton,
  Separator,
  Switch,
  NativeSelect,
  Progress,
  Alert,
} from "@chakra-ui/react"
import { FiSearch, FiRefreshCw, FiMap, FiFilter, FiX } from "react-icons/fi"
import dynamic from "next/dynamic"
import Navbar from "@/components/layout/Navbar"
import Footer from "@/components/layout/Footer"
import ResultsTable from "@/components/prospect/ResultsTable"


// Import dynamique de la carte pour éviter les erreurs SSR
const MapComponent = dynamic(() => import("@/components/prospect/MapComponent"), {
  ssr: false,
  loading: () => (
    <Box
      h="500px"
      bg="bg.subtle"
      rounded="lg"
      display="flex"
      alignItems="center"
      justifyContent="center"
    >
      <Text color="fg.muted">Chargement de la carte...</Text>
    </Box>
  ),
})

// Normaliser l'URL de l'API pour s'assurer qu'elle a un schéma valide
const getApiUrl = () => {
  const url = process.env.NEXT_PUBLIC_API_URL || "https://prospect-backend-three.vercel.app"
  // Si l'URL ne commence pas par http:// ou https://, ajouter le schéma approprié
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    // Pour localhost, utiliser http://, sinon https://
    if (url.includes("localhost") || url.startsWith("127.0.0.1")) {
      return `http://${url}`
    }
    return `https://${url}`
  }
  return url
}

const API_URL = getApiUrl()

export default function ProspectPage() {
  const [searchMode, setSearchMode] = useState("text") // "text" ou "map"
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(0)

  // Paramètres de recherche
  const [where, setWhere] = useState("")
  const [lat, setLat] = useState(null)
  const [lon, setLon] = useState(null)
  const [radiusKm, setRadiusKm] = useState(5)
  const [radiusMinKm, setRadiusMinKm] = useState(0)
  const [tags, setTags] = useState("")
  const [category, setCategory] = useState("")
  const [number, setNumber] = useState(20)
  const [enrichMax, setEnrichMax] = useState(10)
  const [has, setHas] = useState("")
  const [minContacts, setMinContacts] = useState(0)
  const [excludeNames, setExcludeNames] = useState("")
  const [excludeBrands, setExcludeBrands] = useState("")
  const [sort, setSort] = useState("contacts")
  const [dedupe, setDedupe] = useState("smart")
  const [view, setView] = useState("full")
  const [includeCoverage, setIncludeCoverage] = useState(true)

  const abortControllerRef = useRef(null)

  const handleMapClick = useCallback((clickedLat, clickedLon) => {
    setLat(clickedLat)
    setLon(clickedLon)
    setSearchMode("map")
  }, [])

  const buildSearchParams = useCallback(() => {
    const params = new URLSearchParams()

    if (searchMode === "text" && where) {
      params.append("where", where)
    } else if (searchMode === "map" && lat !== null && lon !== null) {
      params.append("lat", lat.toString())
      params.append("lon", lon.toString())
    } else {
      return null
    }

    if (radiusKm > 0) params.append("radius_km", radiusKm.toString())
    if (radiusMinKm > 0) params.append("radius_min_km", radiusMinKm.toString())
    if (tags) params.append("tags", tags)
    if (category) params.append("category", category)
    params.append("number", number.toString())
    params.append("enrich_max", enrichMax.toString())
    if (has) params.append("has", has)
    params.append("min_contacts", minContacts.toString())
    if (excludeNames) params.append("exclude_names", excludeNames)
    if (excludeBrands) params.append("exclude_brands", excludeBrands)
    params.append("sort", sort)
    params.append("dedupe", dedupe)
    params.append("view", view)
    params.append("include_coverage", includeCoverage.toString())

    return params
  }, [
    searchMode,
    where,
    lat,
    lon,
    radiusKm,
    radiusMinKm,
    tags,
    category,
    number,
    enrichMax,
    has,
    minContacts,
    excludeNames,
    excludeBrands,
    sort,
    dedupe,
    view,
    includeCoverage,
  ])

  const performSearchInternal = useCallback(
    async (retryCount = 0) => {
      const params = buildSearchParams()
      if (!params) {
        setError("Veuillez saisir une recherche (texte ou coordonnées)")
        return
      }

      // Annuler la recherche précédente si elle existe
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }

      abortControllerRef.current = new AbortController()
      setLoading(true)
      setError(null)
      setResults(null)
      setProgress(0)

      const MAX_RETRIES = 3
      const RETRY_DELAY = 2000 // 2 secondes entre les tentatives

      try {
        // Simulation de progression
        const progressInterval = setInterval(() => {
          setProgress((prev) => {
            if (prev >= 90) return prev
            return prev + Math.random() * 10
          })
        }, 500)

        const response = await fetch(`${API_URL}/prospects?${params.toString()}`, {
          signal: abortControllerRef.current.signal,
        })

        clearInterval(progressInterval)
        setProgress(100)

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: "Erreur inconnue" }))
          const errorMessage = errorData.detail || `Erreur ${response.status}`

          // Vérifier si c'est une erreur de timeout Overpass
          const isOverpassTimeout =
            errorMessage.includes("Overpass") ||
            errorMessage.includes("overpass") ||
            errorMessage.includes("Timeout") ||
            errorMessage.includes("temps écoulé") ||
            errorMessage.includes("indisponibles") ||
            errorMessage.includes("endpoints Overpass") ||
            errorMessage.includes("overpass-api.de") ||
            errorMessage.includes("overpass.kumi.systems") ||
            errorMessage.includes("overpass.private.coffee")

          // Si c'est un timeout Overpass et qu'on peut réessayer, on réessaie automatiquement
          if (isOverpassTimeout && retryCount < MAX_RETRIES) {
            clearInterval(progressInterval)
            setProgress(0)
            // Attendre avant de réessayer
            await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY * (retryCount + 1)))
            // Réessayer sans afficher l'erreur
            return performSearchInternal(retryCount + 1)
          }

          // Sinon, afficher l'erreur normalement
          throw new Error(errorMessage)
        }

        const data = await response.json()
        setResults(data)
        setProgress(100)
      } catch (err) {
        if (err?.name === "AbortError") return

        const errorMessage = err?.message || "Une erreur est survenue lors de la recherche"

        // Vérifier si c'est une erreur de timeout Overpass
        const isOverpassTimeout =
          errorMessage.includes("Overpass") ||
          errorMessage.includes("overpass") ||
          errorMessage.includes("Timeout") ||
          errorMessage.includes("temps écoulé") ||
          errorMessage.includes("indisponibles") ||
          errorMessage.includes("endpoints Overpass") ||
          errorMessage.includes("overpass-api.de") ||
          errorMessage.includes("overpass.kumi.systems") ||
          errorMessage.includes("overpass.private.coffee")

        // Si c'est un timeout Overpass et qu'on peut réessayer, on réessaie automatiquement
        if (isOverpassTimeout && retryCount < MAX_RETRIES) {
          setProgress(0)
          // Attendre avant de réessayer (délai progressif)
          await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY * (retryCount + 1)))
          // Réessayer sans afficher l'erreur
          return performSearchInternal(retryCount + 1)
        }

        // Afficher l'erreur seulement si on a épuisé les tentatives ou si ce n'est pas un timeout Overpass
        setError(errorMessage)
        setProgress(0)
      } finally {
        if (retryCount === 0 || !abortControllerRef.current?.signal.aborted) {
          setLoading(false)
          setTimeout(() => setProgress(0), 1000)
        }
      }
    },
    [buildSearchParams]
  )

  const performSearch = useCallback(() => {
    return performSearchInternal(0)
  }, [performSearchInternal])

  const handleReset = () => {
    setWhere("")
    setLat(null)
    setLon(null)
    setRadiusKm(5)
    setRadiusMinKm(0)
    setTags("")
    setCategory("")
    setNumber(20)
    setEnrichMax(10)
    setHas("")
    setMinContacts(0)
    setExcludeNames("")
    setExcludeBrands("")
    setSort("contacts")
    setDedupe("smart")
    setView("full")
    setIncludeCoverage(true)
    setResults(null)
    setError(null)
    setSearchMode("text")
  }

  return (
    <Box minH="100vh" bg="bg" color="fg">
      <Navbar />

      <Container maxW="8xl" py="8">
        <VStack gap="8" align="stretch">
          {/* Header */}
          <Box>
            <Heading size="2xl" mb="2" fontWeight="800">
              Prospection intelligente
            </Heading>
            <Text color="fg.muted" fontSize="lg">
              Recherchez et enrichissez vos prospects avec des critères avancés
            </Text>
          </Box>

          {/* Mode de recherche */}
          <Card.Root>
            <Card.Body>
              <VStack gap="6" align="stretch">
                <Box>
                  <Text fontWeight="600" mb="4" fontSize="sm">
                    Mode de recherche
                  </Text>
                  <HStack gap="2" flexWrap="wrap">
                    <Button
                      variant={searchMode === "text" ? "solid" : "outline"}
                      colorPalette={searchMode === "text" ? "blue" : "gray"}
                      onClick={() => setSearchMode("text")}
                      fontWeight="600"
                    >
                      <FiSearch />
                      Recherche par texte
                    </Button>
                    <Button
                      variant={searchMode === "map" ? "solid" : "outline"}
                      colorPalette={searchMode === "map" ? "blue" : "gray"}
                      onClick={() => setSearchMode("map")}
                      fontWeight="600"
                    >
                      <FiMap />
                      Recherche par carte
                    </Button>
                  </HStack>
                </Box>

                {/* Recherche par texte */}
                {searchMode === "text" && (
                  <Box>
                    <Text fontWeight="600" mb="2" fontSize="sm">
                      Recherche libre
                    </Text>
                    <Input
                      placeholder="Ex: restaurants à Paris, hôtels Lyon, pharmacies Marseille..."
                      value={where}
                      onChange={(e) => setWhere(e.target.value)}
                      size="lg"
                      onKeyDown={(e) => e.key === "Enter" && performSearch()}
                    />
                    <Text fontSize="sm" color="fg.muted" mt="2">
                      Saisissez un lieu, une ville, un quartier ou une adresse
                    </Text>
                  </Box>
                )}

                {/* Recherche par carte */}
                {searchMode === "map" && (
                  <VStack gap="4" align="stretch">
                    <Box>
                      <Text fontWeight="600" mb="2" fontSize="sm">
                        Cliquez sur la carte pour sélectionner un point
                      </Text>
                      <MapComponent
                        onMapClick={handleMapClick}
                        selectedLat={lat}
                        selectedLon={lon}
                        radius={radiusKm}
                      />
                      {lat !== null && lon !== null && (
                        <HStack mt="4" p="4" bg="bg.subtle" rounded="lg">
                          <Badge colorPalette="green">Coordonnées sélectionnées</Badge>
                          <Text fontSize="sm" color="fg.muted">
                            Lat: {lat.toFixed(6)}, Lon: {lon.toFixed(6)}
                          </Text>
                          <IconButton
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setLat(null)
                              setLon(null)
                            }}
                            aria-label="Effacer"
                          >
                            <FiX />
                          </IconButton>
                        </HStack>
                      )}
                    </Box>
                  </VStack>
                )}
              </VStack>
            </Card.Body>
          </Card.Root>

          {/* Paramètres avancés */}
          <Card.Root>
            <Card.Body>
              <VStack gap="6" align="stretch">
                <HStack justify="space-between">
                  <Heading size="md" fontWeight="700">
                    <HStack>
                      <FiFilter />
                      <Text>Paramètres de recherche</Text>
                    </HStack>
                  </Heading>
                  <Button size="sm" variant="ghost" onClick={handleReset}>
                    <FiRefreshCw />
                    Réinitialiser
                  </Button>
                </HStack>

                <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap="4">
                  {/* Rayon */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Rayon maximum (km)
                    </Text>
                    <Input
                      type="number"
                      value={radiusKm}
                      onChange={(e) => setRadiusKm(parseInt(e.target.value) || 0)}
                      min={0}
                      max={100}
                    />
                  </Box>

                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Rayon minimum (km)
                    </Text>
                    <Input
                      type="number"
                      value={radiusMinKm}
                      onChange={(e) => setRadiusMinKm(parseInt(e.target.value) || 0)}
                      min={0}
                      max={100}
                    />
                  </Box>

                  {/* Nombre de résultats */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Nombre de résultats
                    </Text>
                    <Input
                      type="number"
                      value={number}
                      onChange={(e) => setNumber(parseInt(e.target.value) || 1)}
                      min={1}
                      max={200}
                    />
                  </Box>

                  {/* Tags OSM */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Tags OSM
                    </Text>
                    <Input
                      placeholder="Ex: restaurant,hotel,spa"
                      value={tags}
                      onChange={(e) => setTags(e.target.value)}
                    />
                    <Text fontSize="xs" color="fg.muted" mt="1">
                      Séparés par des virgules
                    </Text>
                  </Box>

                  {/* Catégorie (NativeSelect v3) */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Catégorie
                    </Text>
                    <NativeSelect.Root>
                      <NativeSelect.Field value={category} onChange={(e) => setCategory(e.target.value)}>
                        <option value="">Toutes</option>
                        <option value="restaurant">Restaurant</option>
                        <option value="hotel">Hôtel</option>
                        <option value="spa">Spa</option>
                        <option value="bakery">Boulangerie</option>
                        <option value="pharmacy">Pharmacie</option>
                        <option value="shop">Magasin</option>
                        <option value="cafe">Café</option>
                      </NativeSelect.Field>
                      <NativeSelect.Indicator />
                    </NativeSelect.Root>
                  </Box>

                  {/* Enrichissement */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Enrichissement max
                    </Text>
                    <Input
                      type="number"
                      value={enrichMax}
                      onChange={(e) => setEnrichMax(parseInt(e.target.value) || 0)}
                      min={0}
                      max={100}
                    />
                    <Text fontSize="xs" color="fg.muted" mt="1">
                      Nombre de prospects à enrichir
                    </Text>
                  </Box>

                  {/* Has */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Doit avoir
                    </Text>
                    <Input placeholder="Ex: website,email,phone" value={has} onChange={(e) => setHas(e.target.value)} />
                    <Text fontSize="xs" color="fg.muted" mt="1">
                      website, email, phone, whatsapp
                    </Text>
                  </Box>

                  {/* Min contacts */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Contacts minimum
                    </Text>
                    <Input
                      type="number"
                      value={minContacts}
                      onChange={(e) => setMinContacts(parseInt(e.target.value) || 0)}
                      min={0}
                      max={10}
                    />
                  </Box>

                  {/* Exclure noms */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Exclure noms
                    </Text>
                    <Input
                      placeholder="Ex: mairie, police"
                      value={excludeNames}
                      onChange={(e) => setExcludeNames(e.target.value)}
                    />
                  </Box>

                  {/* Exclure marques */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Exclure marques
                    </Text>
                    <Input
                      placeholder="Ex: kfc, carrefour"
                      value={excludeBrands}
                      onChange={(e) => setExcludeBrands(e.target.value)}
                    />
                  </Box>

                  {/* Tri */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Tri
                    </Text>
                    <NativeSelect.Root>
                      <NativeSelect.Field value={sort} onChange={(e) => setSort(e.target.value)}>
                        <option value="contacts">Contacts</option>
                        <option value="distance">Distance</option>
                        <option value="name">Nom</option>
                        <option value="random">Aléatoire</option>
                      </NativeSelect.Field>
                      <NativeSelect.Indicator />
                    </NativeSelect.Root>
                  </Box>

                  {/* Déduplication */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Déduplication
                    </Text>
                    <NativeSelect.Root>
                      <NativeSelect.Field value={dedupe} onChange={(e) => setDedupe(e.target.value)}>
                        <option value="none">Aucune</option>
                        <option value="strict">Stricte</option>
                        <option value="smart">Intelligente</option>
                      </NativeSelect.Field>
                      <NativeSelect.Indicator />
                    </NativeSelect.Root>
                  </Box>

                  {/* Vue */}
                  <Box>
                    <Text fontSize="sm" fontWeight="500" mb="2">
                      Vue
                    </Text>
                    <NativeSelect.Root>
                      <NativeSelect.Field value={view} onChange={(e) => setView(e.target.value)}>
                        <option value="full">Complète</option>
                        <option value="light">Légère</option>
                      </NativeSelect.Field>
                      <NativeSelect.Indicator />
                    </NativeSelect.Root>
                  </Box>
                </SimpleGrid>

                <Separator />

                <HStack>
                  <Switch.Root
                    checked={includeCoverage}
                    onCheckedChange={(e) => setIncludeCoverage(e.checked)}
                  >
                    <Switch.HiddenInput />
                    <Switch.Control>
                      <Switch.Thumb />
                    </Switch.Control>
                  </Switch.Root>

                  <Text fontSize="sm" fontWeight="500">
                    Inclure les statistiques de couverture
                  </Text>
                </HStack>
              </VStack>
            </Card.Body>
          </Card.Root>

          {/* Bouton de recherche */}
          <Button
            size="lg"
            colorPalette="blue"
            onClick={performSearch}
            loading={loading}
            loadingText="Recherche en cours..."
            fontWeight="600"
            py="7"
            fontSize="lg"
            disabled={
              loading ||
              (searchMode === "text" && !where) ||
              (searchMode === "map" && (lat === null || lon === null))
            }
          >
            <FiSearch />
            Lancer la prospection
          </Button>

          {/* Barre de progression */}
          {loading && (
            <Card.Root>
              <Card.Body>
                <VStack gap="4">
                  <HStack w="100%" justify="space-between">
                    <Text fontWeight="600">Recherche en cours...</Text>
                    <Text fontSize="sm" color="fg.muted">
                      {Math.round(progress)}%
                    </Text>
                  </HStack>

                  <Progress.Root value={progress} size="lg" colorPalette="cyan" w="100%">
                    <Progress.Track>
                      <Progress.Range />
                    </Progress.Track>
                  </Progress.Root>

                  <Text fontSize="sm" color="fg.muted" textAlign="center">
                    La prospection peut prendre quelques instants selon les critères sélectionnés.
                  </Text>
                </VStack>
              </Card.Body>
            </Card.Root>
          )}

          {/* Erreur */}
          {error && (
            <Alert.Root status="error" variant="surface" borderRadius="lg">
              <Alert.Indicator />
              <Alert.Content>
                <Alert.Title>Erreur</Alert.Title>
                <Alert.Description>{error}</Alert.Description>
              </Alert.Content>
            </Alert.Root>
          )}

          {/* Résultats */}
          {results && !loading && (
            <ResultsTable results={results.results || []} metadata={results} />
          )}
        </VStack>
      </Container>

      <Footer />
    </Box>
  )
}
