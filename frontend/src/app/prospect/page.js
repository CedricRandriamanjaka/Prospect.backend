// src/app/prospect/page.js
"use client"

import { useState, useCallback, useRef } from "react"
import dynamic from "next/dynamic"
import {
  Box,
  Container,
  VStack,
  HStack,
  Text,
  Card,
  Progress,
  Alert,
  Grid,
  GridItem,
} from "@chakra-ui/react"
import { FiMap, FiX } from "react-icons/fi"

import Navbar from "@/components/layout/Navbar"
import Footer from "@/components/layout/Footer"
import ResultsTable from "@/components/prospect/ResultsTable"
import SearchForm from "@/components/prospect/SearchForm"

// Import dynamique de la carte pour éviter SSR
const MapComponent = dynamic(() => import("@/components/prospect/MapComponent"), {
  ssr: false,
  loading: () => (
    <Box
      h="600px"
      bg="bg.subtle"
      rounded="xl"
      display="flex"
      alignItems="center"
      justifyContent="center"
      borderWidth="2px"
      borderColor="border"
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
  const [searchParams, setSearchParams] = useState("")
  const [lat, setLat] = useState(null)
  const [lon, setLon] = useState(null)
  const [radius, setRadius] = useState(5)
  const [radiusMin, setRadiusMin] = useState(0)
  const [showMap, setShowMap] = useState(true)

  const abortControllerRef = useRef(null)

  const handleMapClick = useCallback((clickedLat, clickedLon) => {
    setLat(clickedLat)
    setLon(clickedLon)
  }, [])

  const handleSearch = useCallback(
    async (params) => {
      // Ajouter les coordonnées si sélectionnées
      let finalParams = params

      if (lat !== null && lon !== null) {
        const latLonParams = `lat=${lat}&lon=${lon}`
        if (finalParams) {
          finalParams = `${latLonParams}&${finalParams}`
        } else {
          finalParams = latLonParams
        }
      }

      if (!finalParams && lat === null && lon === null) {
        setError("Veuillez entrer une localisation ou sélectionner une position sur la carte.")
        return
      }

      setSearchParams(finalParams)

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

        const res = await fetch(`${API_URL}/prospects?${finalParams}`, {
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
    },
    [lat, lon]
  )

  const handleReset = () => {
    setSearchParams("")
    setLat(null)
    setLon(null)
    setRadius(5)
    setRadiusMin(0)
    setResults(null)
    setError(null)
  }

  return (
    <Box minH="100vh" display="flex" flexDirection="column" bg="bg.canvas">
      <Navbar />

      <Container maxW="8xl" py="6" flex="1">
        <VStack gap="6" align="stretch">
          {/* Layout principal: Formulaire + Carte côte à côte */}
          <Grid templateColumns={{ base: "1fr", lg: "1fr 1fr" }} gap="6">
            {/* Formulaire de recherche */}
            <GridItem>
              <SearchForm
                onSearch={handleSearch}
                loading={loading}
                onRadiusChange={(newRadius, newRadiusMin) => {
                  setRadius(newRadius)
                  setRadiusMin(newRadiusMin)
                }}
                initialRadius={radius}
                initialRadiusMin={radiusMin}
              />
            </GridItem>

            {/* Carte interactive */}
            <GridItem>
              <Card.Root
                shadow="lg"
                borderWidth="1px"
                borderColor="border.subtle"
                bg="surface"
                _dark={{ bg: "surface", borderColor: "border" }}
                position="relative"
              >
                <Card.Body p="0">
                  <Box position="relative">
                    <MapComponent
                      onMapClick={handleMapClick}
                      selectedLat={lat}
                      selectedLon={lon}
                      radius={radius}
                      radiusMin={radiusMin}
                    />
                    {/* Bouton pour masquer/afficher la carte */}
                    <Box
                      position="absolute"
                      top="4"
                      right="4"
                      zIndex="1000"
                    >
                      <Card.Root size="sm" shadow="md">
                        <Card.Body p="2">
                          <HStack gap="2">
                            <FiMap size="14" color="var(--chakra-colors-fg-muted)" />
                            <Text fontSize="xs" color="fg.muted">
                              Carte
                            </Text>
                          </HStack>
                        </Card.Body>
                      </Card.Root>
                    </Box>
                  </Box>
                </Card.Body>
              </Card.Root>
            </GridItem>
          </Grid>

          {/* Progress bar élégante */}
          {loading && (
            <Card.Root shadow="md" borderWidth="1px" borderColor="border.subtle">
              <Card.Body p="4">
                <VStack gap="3">
                  <HStack w="100%" justify="space-between">
                    <HStack gap="2">
                      <Box
                        w="3"
                        h="3"
                        rounded="full"
                        bg="blue.500"
                        animation="pulse 1.5s ease-in-out infinite"
                      />
                      <Text fontWeight="700" fontSize="sm">
                        Recherche en cours…
                      </Text>
                    </HStack>
                    <Text fontSize="sm" color="fg.muted" fontWeight="600">
                      {Math.round(progress)}%
                    </Text>
                  </HStack>

                  <Progress.Root
                    value={progress}
                    size="lg"
                    w="100%"
                    rounded="full"
                    colorPalette="blue"
                    bg="bg.subtle"
                  >
                    <Progress.Track>
                      <Progress.Range />
                    </Progress.Track>
                  </Progress.Root>

                  <Text fontSize="xs" color="fg.muted" textAlign="center">
                    La durée dépend des paramètres de recherche et de l'enrichissement.
                  </Text>
                </VStack>
              </Card.Body>
            </Card.Root>
          )}

          {/* Erreur */}
          {error && (
            <Alert.Root
              status="error"
              variant="subtle"
              rounded="lg"
              shadow="md"
              borderWidth="1px"
              borderColor="red.200"
              _dark={{ borderColor: "red.800" }}
            >
              <Alert.Indicator />
              <Alert.Content>
                <HStack justify="space-between" align="center" w="100%">
                  <Text fontWeight="600">{error}</Text>
                  <Box
                    as="button"
                    onClick={() => setError(null)}
                    p="1"
                    rounded="md"
                    _hover={{ bg: "bg.subtle" }}
                  >
                    <FiX size="16" />
                  </Box>
                </HStack>
              </Alert.Content>
            </Alert.Root>
          )}

          {/* Résultats */}
          {results && !loading && (
            <Box>
              <ResultsTable results={results.results || []} metadata={results} />
            </Box>
          )}
        </VStack>
      </Container>

      <Footer />

      <style jsx global>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
      `}</style>
    </Box>
  )
}
