// src/app/prospect/page.js
"use client"

import { useState, useCallback, useRef } from "react"
import dynamic from "next/dynamic"
import {
  Box,
  Button,
  Container,
  Heading,
  VStack,
  HStack,
  Text,
  Input,
  SimpleGrid,
  Card,
  IconButton,
  Badge,
  Separator,
  Progress,
  Alert,
  NativeSelect,
} from "@chakra-ui/react"
import { FiSearch, FiRefreshCw, FiMap, FiFilter, FiX, FiInfo } from "react-icons/fi"

import Navbar from "@/components/layout/Navbar"
import Footer from "@/components/layout/Footer"
import ResultsTable from "@/components/prospect/ResultsTable"
import { Tooltip } from "@/components/ui/tooltip"
import { Switch } from "@/components/ui/switch"

// Import dynamique de la carte pour éviter SSR
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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://prospect-backend-three.vercel.app"

const HELP = {
  searchMode:
    "Choisir la méthode. Texte = recherche par lieu. Carte = cliquer un point puis lancer la prospection.",
  where: "Lieu libre: pays, ville, quartier, adresse.",
  radiusKm: "Rayon maximum autour du point ou du lieu. Converti automatiquement en zone rectangulaire (bbox) pour des raisons de performance.",
  radiusMinKm: "Exclut le centre: utile pour éviter trop de résultats très proches.",
  number: "Nombre maximum de résultats retournés par le backend.",
  tags: "Tags OSM séparés par virgules. Exemple: restaurant,hotel,pharmacy",
  category: "Filtre rapide par catégorie (si supporté côté backend).",
  enrichMax:
    "Nombre maximum de prospects à enrichir (scraping site web: email/téléphone). Plus haut = plus lent.",
  has: "Forcer des champs présents. Exemple: website,email,phone,whatsapp",
  minContacts: "Nombre minimum de contacts trouvés (email/phone/website/whatsapp).",
  excludeNames: "Exclure des noms contenant ces mots. Exemple: mairie, police",
  excludeBrands: "Exclure des grandes marques. Exemple: kfc, carrefour",
  sort: "Tri des résultats.",
  dedupe: "Déduplication: none, strict, smart.",
  view: "full = détails complets. light = plus léger/rapide.",
  includeCoverage: "Inclut des statistiques (couverture, timings) si disponibles côté backend.",
}

function HelpIcon({ text }) {
  return (
    <Tooltip content={text} openDelay={250}>
      <Box display="inline-flex">
        <IconButton
          variant="ghost"
          size="xs"
          aria-label="Aide"
          rounded="full"
        >
          <FiInfo />
        </IconButton>
      </Box>
    </Tooltip>
  )
}

export default function ProspectPage() {
  const [searchMode, setSearchMode] = useState("text") // "text" | "map"
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(0)

  // Paramètres
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

    if (searchMode === "text" && where.trim()) {
      params.append("where", where.trim())
    } else if (searchMode === "map" && lat !== null && lon !== null) {
      params.append("lat", String(lat))
      params.append("lon", String(lon))
    } else {
      return null
    }

    if (radiusKm > 0) params.append("radius_km", String(radiusKm))
    if (radiusMinKm > 0) params.append("radius_min_km", String(radiusMinKm))
    if (tags.trim()) params.append("tags", tags.trim())
    if (category) params.append("category", category)

    params.append("number", String(number))
    params.append("enrich_max", String(enrichMax))

    if (has.trim()) params.append("has", has.trim())
    params.append("min_contacts", String(minContacts))

    if (excludeNames.trim()) params.append("exclude_names", excludeNames.trim())
    if (excludeBrands.trim()) params.append("exclude_brands", excludeBrands.trim())

    params.append("sort", sort)
    params.append("dedupe", dedupe)
    params.append("view", view)
    params.append("include_coverage", includeCoverage ? "true" : "false")

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

  const performSearch = useCallback(async () => {
    const params = buildSearchParams()
    if (!params) {
      setError("Saisir un lieu (texte) ou sélectionner un point (carte).")
      return
    }

    if (abortControllerRef.current) abortControllerRef.current.abort()
    abortControllerRef.current = new AbortController()

    setLoading(true)
    setError(null)
    setResults(null)
    setProgress(0)

    let progressInterval = null
    try {
      progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 92) return prev
          const bump = 3 + Math.random() * 9
          return Math.min(92, prev + bump)
        })
      }, 450)

      const res = await fetch(`${API_URL}/prospects?${params.toString()}`, {
        signal: abortControllerRef.current.signal,
      })

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({ detail: "Erreur inconnue" }))
        throw new Error(errJson.detail || `Erreur ${res.status}`)
      }

      const data = await res.json()
      setProgress(100)
      setResults(data)
    } catch (err) {
      if (err?.name === "AbortError") return
      setError(err?.message || "Erreur lors de la recherche.")
      setProgress(0)
    } finally {
      if (progressInterval) clearInterval(progressInterval)
      setLoading(false)
      setTimeout(() => setProgress(0), 900)
    }
  }, [buildSearchParams])

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

  const disabledSearch =
    loading ||
    (searchMode === "text" && !where.trim()) ||
    (searchMode === "map" && (lat === null || lon === null))

  return (
    <Box minH="100vh" bg="bg.canvas" color="fg">
      <Navbar />

      <Container maxW="7xl" py="8">
        <VStack gap="8" align="stretch">
          {/* Header */}
          <Box>
            <Heading size="2xl" mb="2" fontWeight="800">
              Prospection intelligente
            </Heading>
            <Text color="fg.muted" fontSize="lg">
              Rechercher, filtrer, enrichir, exporter.
            </Text>
          </Box>

          {/* Mode de recherche */}
          <Card.Root>
            <Card.Body>
              <VStack gap="6" align="stretch">
                <HStack justify="space-between" align="center">
                  <HStack gap="2">
                    <Heading size="md" fontWeight="800">
                      Mode de recherche
                    </Heading>
                    <HelpIcon text={HELP.searchMode} />
                  </HStack>
                </HStack>

                <HStack gap="2" flexWrap="wrap">
                  <Button
                    variant={searchMode === "text" ? "solid" : "outline"}
                    colorPalette={searchMode === "text" ? "blue" : "gray"}
                    onClick={() => setSearchMode("text")}
                  >
                    <FiSearch />
                    <Box as="span" ml="2">
                      Texte
                    </Box>
                  </Button>

                  <Button
                    variant={searchMode === "map" ? "solid" : "outline"}
                    colorPalette={searchMode === "map" ? "blue" : "gray"}
                    onClick={() => setSearchMode("map")}
                  >
                    <FiMap />
                    <Box as="span" ml="2">
                      Carte
                    </Box>
                  </Button>
                </HStack>

                {searchMode === "text" && (
                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontWeight="600" fontSize="sm">
                        Recherche libre
                      </Text>
                      <HelpIcon text={HELP.where} />
                    </HStack>
                    <Input
                      placeholder="Ex: hôtels Port Louis, pharmacies Curepipe, restaurants Grand Baie..."
                      value={where}
                      onChange={(e) => setWhere(e.target.value)}
                      size="lg"
                      onKeyDown={(e) => e.key === "Enter" && performSearch()}
                    />
                    <Text fontSize="sm" color="fg.muted" mt="2">
                      Lieu, ville, quartier ou adresse.
                    </Text>
                  </Box>
                )}

                {searchMode === "map" && (
                  <VStack gap="4" align="stretch">
                    <Text fontWeight="600" fontSize="sm">
                      Cliquer sur la carte pour choisir un point
                    </Text>

                    <MapComponent
                      onMapClick={handleMapClick}
                      selectedLat={lat}
                      selectedLon={lon}
                      radius={radiusKm}
                    />

                    {lat !== null && lon !== null && (
                      <HStack mt="2" p="3" bg="bg.subtle" rounded="lg" justify="space-between">
                        <HStack gap="3">
                          <Badge colorPalette="green">Point sélectionné</Badge>
                          <Text fontSize="sm" color="fg.muted">
                            Lat: {lat.toFixed(6)} · Lon: {lon.toFixed(6)}
                          </Text>
                        </HStack>
                        <IconButton
                          size="sm"
                          variant="ghost"
                          aria-label="Effacer le point"
                          onClick={() => {
                            setLat(null)
                            setLon(null)
                          }}
                        >
                          <FiX />
                        </IconButton>
                      </HStack>
                    )}
                  </VStack>
                )}
              </VStack>
            </Card.Body>
          </Card.Root>

          {/* Paramètres avancés */}
          <Card.Root>
            <Card.Body>
              <VStack gap="6" align="stretch">
                <HStack justify="space-between" align="center">
                  <HStack gap="2">
                    <FiFilter />
                    <Heading size="md" fontWeight="800">
                      Paramètres
                    </Heading>
                  </HStack>

                  <Button size="sm" variant="ghost" onClick={handleReset}>
                    <FiRefreshCw />
                    <Box as="span" ml="2">
                      Réinitialiser
                    </Box>
                  </Button>
                </HStack>

                <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap="4">
                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Rayon maximum (km)
                      </Text>
                      <HelpIcon text={HELP.radiusKm} />
                    </HStack>
                    <Input
                      type="number"
                      value={radiusKm}
                      onChange={(e) => setRadiusKm(parseInt(e.target.value || "0", 10) || 0)}
                      min={0}
                      max={100}
                    />
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Rayon minimum (km)
                      </Text>
                      <HelpIcon text={HELP.radiusMinKm} />
                    </HStack>
                    <Input
                      type="number"
                      value={radiusMinKm}
                      onChange={(e) => setRadiusMinKm(parseInt(e.target.value || "0", 10) || 0)}
                      min={0}
                      max={100}
                    />
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Nombre de résultats
                      </Text>
                      <HelpIcon text={HELP.number} />
                    </HStack>
                    <Input
                      type="number"
                      value={number}
                      onChange={(e) => setNumber(parseInt(e.target.value || "1", 10) || 1)}
                      min={1}
                      max={200}
                    />
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Tags OSM
                      </Text>
                      <HelpIcon text={HELP.tags} />
                    </HStack>
                    <Input
                      placeholder="Ex: restaurant,hotel,spa"
                      value={tags}
                      onChange={(e) => setTags(e.target.value)}
                    />
                    <Text fontSize="xs" color="fg.muted" mt="1">
                      Séparer par des virgules.
                    </Text>
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Catégorie
                      </Text>
                      <HelpIcon text={HELP.category} />
                    </HStack>

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
                    </NativeSelect.Root>
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Enrichissement max
                      </Text>
                      <HelpIcon text={HELP.enrichMax} />
                    </HStack>
                    <Input
                      type="number"
                      value={enrichMax}
                      onChange={(e) => setEnrichMax(parseInt(e.target.value || "0", 10) || 0)}
                      min={0}
                      max={300}
                    />
                    <Text fontSize="xs" color="fg.muted" mt="1">
                      Plus haut = plus lent.
                    </Text>
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Doit avoir
                      </Text>
                      <HelpIcon text={HELP.has} />
                    </HStack>
                    <Input
                      placeholder="Ex: website,email,phone"
                      value={has}
                      onChange={(e) => setHas(e.target.value)}
                    />
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Contacts minimum
                      </Text>
                      <HelpIcon text={HELP.minContacts} />
                    </HStack>
                    <Input
                      type="number"
                      value={minContacts}
                      onChange={(e) => setMinContacts(parseInt(e.target.value || "0", 10) || 0)}
                      min={0}
                      max={10}
                    />
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Exclure noms
                      </Text>
                      <HelpIcon text={HELP.excludeNames} />
                    </HStack>
                    <Input
                      placeholder="Ex: mairie, police"
                      value={excludeNames}
                      onChange={(e) => setExcludeNames(e.target.value)}
                    />
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Exclure marques
                      </Text>
                      <HelpIcon text={HELP.excludeBrands} />
                    </HStack>
                    <Input
                      placeholder="Ex: kfc, carrefour"
                      value={excludeBrands}
                      onChange={(e) => setExcludeBrands(e.target.value)}
                    />
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Tri
                      </Text>
                      <HelpIcon text={HELP.sort} />
                    </HStack>
                    <NativeSelect.Root>
                      <NativeSelect.Field value={sort} onChange={(e) => setSort(e.target.value)}>
                        <option value="contacts">Contacts</option>
                        <option value="distance">Distance</option>
                        <option value="name">Nom</option>
                        <option value="random">Aléatoire</option>
                      </NativeSelect.Field>
                    </NativeSelect.Root>
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Déduplication
                      </Text>
                      <HelpIcon text={HELP.dedupe} />
                    </HStack>
                    <NativeSelect.Root>
                      <NativeSelect.Field value={dedupe} onChange={(e) => setDedupe(e.target.value)}>
                        <option value="none">Aucune</option>
                        <option value="strict">Stricte</option>
                        <option value="smart">Intelligente</option>
                      </NativeSelect.Field>
                    </NativeSelect.Root>
                  </Box>

                  <Box>
                    <HStack mb="2" gap="2">
                      <Text fontSize="sm" fontWeight="600">
                        Vue
                      </Text>
                      <HelpIcon text={HELP.view} />
                    </HStack>
                    <NativeSelect.Root>
                      <NativeSelect.Field value={view} onChange={(e) => setView(e.target.value)}>
                        <option value="full">Complète</option>
                        <option value="light">Légère</option>
                      </NativeSelect.Field>
                    </NativeSelect.Root>
                  </Box>
                </SimpleGrid>

                <Separator />

                <HStack justify="space-between" align="center" flexWrap="wrap" gap="3">
                  <HStack gap="2">
                    <Switch
                      checked={includeCoverage}
                      onCheckedChange={setIncludeCoverage}
                      label="Inclure les statistiques de couverture"
                    />
                    <HelpIcon text={HELP.includeCoverage} />
                  </HStack>
                </HStack>
              </VStack>
            </Card.Body>
          </Card.Root>

          {/* Bouton */}
          <Button
            size="xl"
            colorPalette="blue"
            onClick={performSearch}
            loading={loading}
            loadingText="Recherche..."
            disabled={disabledSearch}
          >
            <FiSearch />
            <Box as="span" ml="2">
              Lancer la prospection
            </Box>
          </Button>

          {/* Progress */}
          {loading && (
            <Card.Root>
              <Card.Body>
                <VStack gap="4">
                  <HStack w="100%" justify="space-between">
                    <Text fontWeight="700">Recherche en cours…</Text>
                    <Text fontSize="sm" color="fg.muted">
                      {Math.round(progress)}%
                    </Text>
                  </HStack>

                  <Progress.Root value={progress} size="lg" w="100%" rounded="full" colorPalette="blue">
                    <Progress.Track>
                      <Progress.Range />
                    </Progress.Track>
                  </Progress.Root>

                  <Text fontSize="sm" color="fg.muted" textAlign="center">
                    La durée dépend du rayon, du nombre demandé et de l’enrichissement.
                  </Text>
                </VStack>
              </Card.Body>
            </Card.Root>
          )}

          {/* Erreur */}
          {error && (
            <Alert.Root status="error" variant="subtle" rounded="lg">
              <Alert.Indicator />
              <Alert.Content>{error}</Alert.Content>
            </Alert.Root>
          )}

          {/* Résultats */}
          {results && !loading && (
            <ResultsTable
              results={results.results || []}
              metadata={results}
            />
          )}
        </VStack>
      </Container>

      <Footer />
    </Box>
  )
}
