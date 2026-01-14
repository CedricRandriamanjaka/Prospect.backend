// src/components/prospect/MapComponent.jsx
"use client"

import { useEffect } from "react"
import { Box } from "@chakra-ui/react"
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

export default function MapComponent({ onMapClick, selectedLat, selectedLon, radius = 5 }) {
  const defaultCenter = [48.8566, 2.3522] // Paris
  const defaultZoom = 6

  const hasPoint = selectedLat !== null && selectedLon !== null
  const center = hasPoint ? [selectedLat, selectedLon] : defaultCenter
  const zoom = hasPoint ? 13 : defaultZoom

  return (
    <Box
      h="500px"
      w="100%"
      rounded="lg"
      overflow="hidden"
      borderWidth="1px"
      borderColor="border"
      bg="bg.subtle"
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
            {radius > 0 ? (
              <Circle
                center={[selectedLat, selectedLon]}
                radius={radius * 1000}
                pathOptions={{
                  color: "#0ea5e9",
                  fillColor: "#0ea5e9",
                  fillOpacity: 0.18,
                  weight: 2,
                }}
              />
            ) : null}
          </>
        ) : null}
      </MapContainer>
    </Box>
  )
}
