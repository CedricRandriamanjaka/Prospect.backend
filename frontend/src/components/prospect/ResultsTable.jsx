// src/components/prospect/ResultsTable.jsx
"use client"

import { useMemo, useState } from "react"
import {
  Box,
  Heading,
  VStack,
  HStack,
  Text,
  Button,
  Badge,
  Card,
  Input,
  NativeSelect,
  Stat,
  Table,
} from "@chakra-ui/react"
import { FiDownload, FiMail, FiPhone, FiGlobe, FiMapPin, FiArrowUp, FiArrowDown } from "react-icons/fi"
import * as XLSX from "xlsx"
import { Tooltip } from "@/components/ui/tooltip"

// Fonction pour normaliser les données de l'API vers le format attendu
const normalizeItem = (item) => {
  const adresse = item?.adresse || {}
  const addressStr = [
    adresse.housenumber,
    adresse.street,
    adresse.postcode,
    adresse.city,
  ].filter(Boolean).join(", ")

  return {
    // Données originales
    ...item,
    // Données normalisées pour l'affichage
    name: item?.nom || "-",
    address: addressStr || "-",
    city: adresse.city || "-",
    postcode: adresse.postcode || null,
    category: item?.activite_valeur || item?.activite_type || "-",
    website: item?.site || null,
    email: item?.emails?.[0] || null,
    emails: item?.emails || [],
    phone: item?.telephones?.[0] || null,
    telephones: item?.telephones || [],
    whatsapp: item?.whatsapp || [],
    distance: item?.sales?.distance_km || null,
    contacts_count: item?.sales?.contact_methods_count || 0,
  }
}

export default function ResultsTable({ results = [], metadata = {} }) {
  const [searchTerm, setSearchTerm] = useState("")
  const [sortKey, setSortKey] = useState("")
  const [sortDir, setSortDir] = useState("asc")

  // Normaliser les résultats
  const normalizedResults = useMemo(() => {
    return Array.isArray(results) ? results.map(normalizeItem) : []
  }, [results])

  const filteredResults = useMemo(() => {
    let out = [...normalizedResults]

    // Filtrage par recherche
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase()
      out = out.filter((item) => {
        const name = (item?.name || "").toLowerCase()
        const address = (item?.address || "").toLowerCase()
        const city = (item?.city || "").toLowerCase()
        const category = (item?.category || "").toLowerCase()
        const email = (item?.email || "").toLowerCase()
        const phone = (item?.phone || "").toLowerCase()
        return (
          name.includes(term) ||
          address.includes(term) ||
          city.includes(term) ||
          category.includes(term) ||
          email.includes(term) ||
          phone.includes(term)
        )
      })
    }

    // Tri
    if (sortKey) {
      out.sort((a, b) => {
        let av = a?.[sortKey]
        let bv = b?.[sortKey]

        // Gestion spéciale pour les nombres
        if (sortKey === "contacts_count" || sortKey === "distance") {
          av = Number(av) || 0
          bv = Number(bv) || 0
          return sortDir === "asc" ? av - bv : bv - av
        }

        // Tri textuel
        av = (av ?? "").toString()
        bv = (bv ?? "").toString()
        const cmp = av.localeCompare(bv, undefined, {
          numeric: true,
          sensitivity: "base",
        })
        return sortDir === "asc" ? cmp : -cmp
      })
    }

    return out
  }, [normalizedResults, searchTerm, sortKey, sortDir])

  const getContactCount = (item) => {
    return item?.contacts_count || 0
  }

  const exportToExcel = () => {
    // Préparer les données pour Excel
    const excelData = filteredResults.map((item) => ({
      Nom: item.name,
      Adresse: item.address,
      Ville: item.city,
      "Code postal": item.postcode || "",
      Catégorie: item.category,
      Site: item.website || "",
      Email: item.emails.join("; ") || "",
      Téléphone: item.telephones.join("; ") || "",
      WhatsApp: item.whatsapp.join("; ") || "",
      "Nombre contacts": getContactCount(item),
      Distance: item.distance ? `${item.distance.toFixed(2)} km` : "",
      "Lien OSM": item.osm || "",
    }))

    // Créer le workbook
    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.json_to_sheet(excelData)

    // Ajuster la largeur des colonnes
    const colWidths = [
      { wch: 30 }, // Nom
      { wch: 40 }, // Adresse
      { wch: 20 }, // Ville
      { wch: 12 }, // Code postal
      { wch: 20 }, // Catégorie
      { wch: 30 }, // Site
      { wch: 30 }, // Email
      { wch: 20 }, // Téléphone
      { wch: 20 }, // WhatsApp
      { wch: 15 }, // Nombre contacts
      { wch: 12 }, // Distance
      { wch: 40 }, // Lien OSM
    ]
    ws["!cols"] = colWidths

    // Ajouter la feuille au workbook
    XLSX.utils.book_append_sheet(wb, ws, "Prospects")

    // Ajouter une feuille de métadonnées
    const metaData = [
      { Champ: "Recherche", Valeur: metadata?.query?.where || metadata?.query?.city || "Coordonnées" },
      { Champ: "Nombre total", Valeur: metadata?.count || filteredResults.length },
      { Champ: "Temps d'exécution", Valeur: metadata?.timings?.total_seconds ? `${metadata.timings.total_seconds}s` : "" },
      { Champ: "Enrichis", Valeur: metadata?.timings?.enrichment?.enriched_count || 0 },
      { Champ: "Date d'export", Valeur: new Date().toLocaleString("fr-FR") },
    ]
    const metaWs = XLSX.utils.json_to_sheet(metaData)
    XLSX.utils.book_append_sheet(wb, metaWs, "Métadonnées")

    // Télécharger
    const fileName = `prospects-${new Date().toISOString().split("T")[0]}.xlsx`
    XLSX.writeFile(wb, fileName)
  }

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortKey(key)
      setSortDir("asc")
    }
  }

  const SortIcon = ({ columnKey }) => {
    if (sortKey !== columnKey) return null
    return sortDir === "asc" ? <FiArrowUp size="14" /> : <FiArrowDown size="14" />
  }

  return (
    <VStack gap="6" align="stretch">
      {/* Header + stats */}
      <Card.Root>
        <Card.Body>
          <VStack gap="5" align="stretch">
            <HStack justify="space-between" align="center" flexWrap="wrap" gap="3">
              <Heading size="lg" fontWeight="800">
                Résultats
              </Heading>

              <Button colorPalette="blue" onClick={exportToExcel}>
                <FiDownload />
                <Box as="span" ml="2">
                  Export Excel
                </Box>
              </Button>
            </HStack>

            <Box>
              <Box display="grid" gridTemplateColumns={{ base: "repeat(2, 1fr)", md: "repeat(4, 1fr)" }} gap="4">
                <Stat.Root>
                  <Stat.Label>Total trouvé</Stat.Label>
                  <Stat.ValueText>{metadata?.count || results.length}</Stat.ValueText>
                  <Stat.HelpText>prospects</Stat.HelpText>
                </Stat.Root>

                <Stat.Root>
                  <Stat.Label>Affichés</Stat.Label>
                  <Stat.ValueText>{filteredResults.length}</Stat.ValueText>
                  <Stat.HelpText>après filtrage</Stat.HelpText>
                </Stat.Root>

                {metadata?.timings?.total_seconds != null && (
                  <Stat.Root>
                    <Stat.Label>Temps</Stat.Label>
                    <Stat.ValueText>{metadata.timings.total_seconds}s</Stat.ValueText>
                    <Stat.HelpText>exécution</Stat.HelpText>
                  </Stat.Root>
                )}

                {metadata?.enrich_max > 0 && (
                  <Stat.Root>
                    <Stat.Label>Enrichis</Stat.Label>
                    <Stat.ValueText>{metadata?.timings?.enrichment?.enriched_count || 0}</Stat.ValueText>
                    <Stat.HelpText>prospects</Stat.HelpText>
                  </Stat.Root>
                )}
              </Box>
            </Box>
          </VStack>
        </Card.Body>
      </Card.Root>

      {/* Filters */}
      <Card.Root>
        <Card.Body>
          <HStack gap="4" flexWrap="wrap">
            <Box flex="1" minW="220px">
              <Input
                placeholder="Rechercher dans les résultats…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </Box>

            <NativeSelect.Root w={{ base: "100%", md: "240px" }}>
              <NativeSelect.Field
                value={sortKey}
                onChange={(e) => {
                  const val = e.target.value
                  if (!val) {
                    setSortKey("")
                    setSortDir("asc")
                  } else {
                    handleSort(val)
                  }
                }}
              >
                <option value="">Trier par…</option>
                <option value="name">Nom</option>
                <option value="city">Ville</option>
                <option value="category">Catégorie</option>
                <option value="contacts_count">Contacts</option>
                <option value="distance">Distance</option>
              </NativeSelect.Field>
            </NativeSelect.Root>

            {sortKey ? (
              <Badge colorPalette="blue" variant="subtle">
                {sortDir === "asc" ? "↑" : "↓"} {sortKey}
              </Badge>
            ) : null}
          </HStack>
        </Card.Body>
      </Card.Root>

      {/* Table */}
      <Card.Root>
        <Card.Body p="0">
          <Box overflowX="auto">
            <Table.Root size="sm" variant="outline">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader
                    cursor="pointer"
                    onClick={() => handleSort("name")}
                    _hover={{ bg: "bg.subtle" }}
                  >
                    <HStack gap="2">
                      <Box>Nom</Box>
                      <SortIcon columnKey="name" />
                    </HStack>
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>Adresse</Table.ColumnHeader>
                  <Table.ColumnHeader
                    cursor="pointer"
                    onClick={() => handleSort("city")}
                    _hover={{ bg: "bg.subtle" }}
                  >
                    <HStack gap="2">
                      <Box>Ville</Box>
                      <SortIcon columnKey="city" />
                    </HStack>
                  </Table.ColumnHeader>
                  <Table.ColumnHeader
                    cursor="pointer"
                    onClick={() => handleSort("category")}
                    _hover={{ bg: "bg.subtle" }}
                  >
                    <HStack gap="2">
                      <Box>Catégorie</Box>
                      <SortIcon columnKey="category" />
                    </HStack>
                  </Table.ColumnHeader>
                  <Table.ColumnHeader
                    cursor="pointer"
                    onClick={() => handleSort("contacts_count")}
                    _hover={{ bg: "bg.subtle" }}
                  >
                    <HStack gap="2">
                      <Box>Contacts</Box>
                      <SortIcon columnKey="contacts_count" />
                    </HStack>
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>Détails</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>

              <Table.Body>
                {filteredResults.length === 0 ? (
                  <Table.Row>
                    <Table.Cell colSpan={6}>
                      <Box py="8" textAlign="center">
                        <Text color="fg.muted">Aucun résultat</Text>
                      </Box>
                    </Table.Cell>
                  </Table.Row>
                ) : (
                  filteredResults.map((item, idx) => (
                    <Table.Row key={item?.entity_key || idx}>
                      <Table.Cell fontWeight="700">{item?.name || "-"}</Table.Cell>

                      <Table.Cell>
                        <VStack align="start" gap="1">
                          {item?.address && item.address !== "-" ? (
                            <HStack gap="2">
                              <FiMapPin size="12" />
                              <Text fontSize="sm">{item.address}</Text>
                            </HStack>
                          ) : (
                            <Text fontSize="sm" color="fg.muted">
                              -
                            </Text>
                          )}
                        </VStack>
                      </Table.Cell>

                      <Table.Cell>{item?.city || "-"}</Table.Cell>

                      <Table.Cell>
                        {item?.category && item.category !== "-" ? (
                          <Badge colorPalette="blue" variant="subtle">
                            {item.category}
                          </Badge>
                        ) : (
                          <Text fontSize="sm" color="fg.muted">
                            -
                          </Text>
                        )}
                      </Table.Cell>

                      <Table.Cell>
                        <VStack align="start" gap="2">
                          <Badge colorPalette="green" variant="solid">
                            {getContactCount(item)} contact{getContactCount(item) > 1 ? "s" : ""}
                          </Badge>

                          <HStack gap="2" flexWrap="wrap">
                            {item?.website ? (
                              <Tooltip content={item.website}>
                                <Badge variant="outline" colorPalette="blue" cursor="pointer">
                                  <FiGlobe size="10" />
                                </Badge>
                              </Tooltip>
                            ) : null}

                            {item?.emails.length > 0 ? (
                              <Tooltip content={item.emails.join(", ")}>
                                <Badge variant="outline" colorPalette="purple" cursor="pointer">
                                  <FiMail size="10" />
                                </Badge>
                              </Tooltip>
                            ) : null}

                            {item?.telephones.length > 0 ? (
                              <Tooltip content={item.telephones.join(", ")}>
                                <Badge variant="outline" colorPalette="green" cursor="pointer">
                                  <FiPhone size="10" />
                                </Badge>
                              </Tooltip>
                            ) : null}

                            {item?.whatsapp.length > 0 ? (
                              <Tooltip content={item.whatsapp.join(", ")}>
                                <Badge variant="outline" colorPalette="green" cursor="pointer">
                                  WhatsApp
                                </Badge>
                              </Tooltip>
                            ) : null}
                          </HStack>
                        </VStack>
                      </Table.Cell>

                      <Table.Cell>
                        <VStack align="start" gap="1">
                          {item?.website ? (
                            <Text
                              fontSize="xs"
                              color="blue.600"
                              as="a"
                              href={item.website}
                              target="_blank"
                              rel="noreferrer"
                            >
                              {item.website}
                            </Text>
                          ) : null}

                          {item?.emails.length > 0 ? (
                            <Text fontSize="xs" color="fg.muted">
                              {item.emails[0]}
                              {item.emails.length > 1 && ` (+${item.emails.length - 1})`}
                            </Text>
                          ) : null}

                          {item?.telephones.length > 0 ? (
                            <Text fontSize="xs" color="fg.muted">
                              {item.telephones[0]}
                              {item.telephones.length > 1 && ` (+${item.telephones.length - 1})`}
                            </Text>
                          ) : null}

                          {item?.distance != null ? (
                            <Text fontSize="xs" color="fg.muted">
                              {Number(item.distance).toFixed(2)} km
                            </Text>
                          ) : null}
                        </VStack>
                      </Table.Cell>
                    </Table.Row>
                  ))
                )}
              </Table.Body>
            </Table.Root>
          </Box>
        </Card.Body>
      </Card.Root>
    </VStack>
  )
}
