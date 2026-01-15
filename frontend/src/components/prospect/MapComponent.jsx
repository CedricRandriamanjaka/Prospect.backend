// src/components/prospect/MapComponent.jsx
"use client"

import { useEffect } from "react"
import { Box, Text, VStack } from "@chakra-ui/react"
import { MapContainer, TileLayer, Marker, Circle, useMapEvents, useMap } from "react-leaflet"
import L from "leaflet"
import "leaflet/dist/leaflet.css"

// Fix icônes Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
})

function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => {
      const { lat, lng } = e.latlng
      onMapClick?.(lat, lng)
    },
  })
  return null
}

function MapCenter({ center, zoom }) {
  const map = useMap()
  useEffect(() => {
    if (center) map.setView(center, zoom || map.getZoom())
  }, [map, center, zoom])
  return null
}

export default function MapComponent({ onMapClick, selectedLat, selectedLon, radius = 5, radiusMin = 0 }) {
  const defaultCenter = [48.8566, 2.3522] // Paris
  const defaultZoom = 6

  const hasPoint = selectedLat !== null && selectedLon !== null
  const center = hasPoint ? [selectedLat, selectedLon] : defaultCenter
  const zoom = hasPoint ? 13 : defaultZoom

  return (
    <Box
      h="600px"
      w="100%"
      rounded="xl"
      overflow="hidden"
      borderWidth="2px"
      borderColor="border"
      bg="bg.subtle"
      shadow="lg"
      position="relative"
      _dark={{ borderColor: "border" }}
    >
      <MapContainer center={center} zoom={zoom} style={{ height: "100%", width: "100%" }} scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapClickHandler onMapClick={onMapClick} />
        <MapCenter center={center} zoom={zoom} />

        {hasPoint ? (
          <>
            <Marker position={[selectedLat, selectedLon]} />
            {radius > 0 && (
              <Circle
                center={[selectedLat, selectedLon]}
                radius={radius * 1000}
                pathOptions={{
                  color: "#3b82f6",
                  fillColor: "#3b82f6",
                  fillOpacity: 0.15,
                  weight: 3,
                }}
              />
            )}
            {radiusMin > 0 && (
              <Circle
                center={[selectedLat, selectedLon]}
                radius={radiusMin * 1000}
                pathOptions={{
                  color: "#60a5fa",
                  fillColor: "#60a5fa",
                  fillOpacity: 0.1,
                  weight: 2,
                  dashArray: "5, 5",
                }}
              />
            )}
          </>
        ) : null}
      </MapContainer>

      {/* Overlay avec instructions */}
      {!hasPoint && (
        <Box
          position="absolute"
          top="4"
          left="4"
          right="4"
          bg="white"
          _dark={{ bg: "gray.800" }}
          p="3"
          rounded="lg"
          shadow="md"
          borderWidth="1px"
          borderColor="border"
          zIndex="1000"
        >
          <Text fontSize="sm" fontWeight="600" color="blue.600" _dark={{ color: "blue.400" }}>
            🗺️ Cliquez sur la carte pour sélectionner une position
          </Text>
        </Box>
      )}

      {hasPoint && (
        <Box
          position="absolute"
          bottom="4"
          left="4"
          bg="white"
          _dark={{ bg: "gray.800" }}
          p="3"
          rounded="lg"
          shadow="md"
          borderWidth="1px"
          borderColor="border"
          zIndex="1000"
        >
          <VStack align="start" gap="1">
            <Text fontSize="xs" fontWeight="600" color="fg.muted">
              Position sélectionnée
            </Text>
            <Text fontSize="sm" fontWeight="700">
              {selectedLat.toFixed(6)}, {selectedLon.toFixed(6)}
            </Text>
            {radius > 0 && (
              <Text fontSize="xs" color="blue.600" _dark={{ color: "blue.400" }}>
                Rayon: {radiusMin > 0 ? `${radiusMin}-${radius} km` : `${radius} km`}
              </Text>
            )}
          </VStack>
        </Box>
      )}
    </Box>
  )
}
