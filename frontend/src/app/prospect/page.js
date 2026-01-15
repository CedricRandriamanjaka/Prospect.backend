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
  Card,
  Progress,
  Alert,
} from "@chakra-ui/react"
import { FiSearch, FiRefreshCw, FiMap } from "react-icons/fi"

import Navbar from "@/components/layout/Navbar"
import Footer from "@/components/layout/Footer"
import ResultsTable from "@/components/prospect/ResultsTable"

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

export default function ProspectPage() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(0)
  const [queryParams, setQueryParams] = useState("")
  const [lat, setLat] = useState(null)
  const [lon, setLon] = useState(null)

  const abortControllerRef = useRef(null)

  const handleMapClick = useCallback((clickedLat, clickedLon) => {
    setLat(clickedLat)
    setLon(clickedLon)
  }, [])

  const performSearch = useCallback(async () => {
    // Construire les paramètres
    let params = queryParams.trim()

    // Si lat/lon sont définis, les ajouter
    if (lat !== null && lon !== null) {
      const latLonParams = `lat=${lat}&lon=${lon}`
      if (params) {
        params = `${latLonParams}&${params}`
      } else {
        params = latLonParams
      }
    }

    if (!params) {
      setError("Entrer des paramètres de recherche ou sélectionner une position sur la carte.")
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

      const res = await fetch(`${API_URL}/prospects?${params}`, {
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
  }, [queryParams, lat, lon])

  const handleReset = () => {
    setQueryParams("")
    setLat(null)
    setLon(null)
    setResults(null)
    setError(null)
  }

  return (
    <Box minH="100vh" display="flex" flexDirection="column">
      <Navbar />

      <Container maxW="7xl" py="8" flex="1">
        <VStack gap="6" align="stretch">
          <Heading size="2xl" fontWeight="800" textAlign="center">
            Prospection de Prospects
          </Heading>

          {/* Carte pour sélectionner la position */}
          <Card.Root>
            <Card.Body>
              <VStack gap="4" align="stretch">
                <HStack justify="space-between" align="center">
                  <Heading size="md" fontWeight="700">
                    Sélectionner une position (optionnel)
                  </Heading>
                  {lat !== null && lon !== null && (
                    <Text fontSize="sm" color="fg.muted">
                      Position: {lat.toFixed(6)}, {lon.toFixed(6)}
                    </Text>
                  )}
                </HStack>
                <MapComponent
                  onMapClick={handleMapClick}
                  selectedLat={lat}
                  selectedLon={lon}
                />
                <Text fontSize="sm" color="fg.muted" textAlign="center">
                  Cliquez sur la carte pour sélectionner une position. Les coordonnées seront ajoutées automatiquement aux paramètres.
                </Text>
              </VStack>
            </Card.Body>
          </Card.Root>

          {/* Input pour les paramètres */}
          <Card.Root>
            <Card.Body>
              <VStack gap="4" align="stretch">
                <Heading size="md" fontWeight="700">
                  Paramètres de recherche
                </Heading>

                <Box>
                  <Text fontSize="sm" fontWeight="600" mb="2">
                    Paramètres URL (après le `?`)
                  </Text>
                  <Input
                    placeholder="Ex: where=Maurice&radius_min_km=0&radius_km=5&tags=shop=beauty,shop=cosmetics,shop=perfumery&number=200"
                    value={queryParams}
                    onChange={(e) => setQueryParams(e.target.value)}
                    size="lg"
                  />
                  <Text fontSize="xs" color="fg.muted" mt="2">
                    Exemples:
                    <br />
                    • <code>where=Maurice&category=hotel&has=website&min_contacts=1&number=30&enrich_max=5</code>
                    <br />
                    • <code>where=Paris&radius_min_km=0&radius_km=2&category=restaurant&number=20</code>
                    <br />
                    • <code>tags=shop=beauty,shop=cosmetics&number=100</code>
                  </Text>
                </Box>

                <HStack gap="3" justify="flex-end">
                  <Button variant="outline" onClick={handleReset} disabled={loading}>
                    <FiRefreshCw />
                    <Box as="span" ml="2">
                      Réinitialiser
                    </Box>
                  </Button>
                  <Button
                    colorPalette="blue"
                    size="lg"
                    onClick={performSearch}
                    loading={loading}
                    loadingText="Recherche..."
                    disabled={loading || (!queryParams.trim() && lat === null)}
                  >
                    <FiSearch />
                    <Box as="span" ml="2">
                      Lancer la recherche
                    </Box>
                  </Button>
                </HStack>
              </VStack>
            </Card.Body>
          </Card.Root>

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
                    La durée dépend des paramètres de recherche et de l'enrichissement.
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
