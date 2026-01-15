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
  Separator,
  Link,
} from "@chakra-ui/react"
import {
  FiDownload,
  FiMail,
  FiPhone,
  FiGlobe,
  FiMapPin,
  FiArrowUp,
  FiArrowDown,
  FiClock,
  FiStar,
  FiChevronDown,
  FiChevronUp,
  FiExternalLink,
  FiTag,
  FiCreditCard,
  FiShoppingBag,
  FiBuilding,
} from "react-icons/fi"
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
  ]
    .filter(Boolean)
    .join(", ")

  return {
    // Données originales
    ...item,
    // Données normalisées pour l'affichage
    name: item?.nom || "-",
    address: addressStr || adresse.full || "-",
    city: adresse.city || "-",
    postcode: adresse.postcode || null,
    category: item?.activite_valeur || item?.activite_type || "-",
    categoryType: item?.activite_type || "-",
    website: item?.site || null,
    email: item?.emails?.[0] || null,
    emails: item?.emails || [],
    phone: item?.telephones?.[0] || null,
    telephones: item?.telephones || [],
    whatsapp: item?.whatsapp || [],
    horaires: item?.horaires || null,
    cuisine: item?.cuisine || null,
    etoiles: item?.etoiles || null,
    operateur: item?.operateur || null,
    marque: item?.marque || null,
    lat: item?.lat || null,
    lon: item?.lon || null,
    osm: item?.osm || null,
    source: item?.source || null,
    extras: item?.extras || {},
    payment: item?.payment || {},
    contacts_social: item?.contacts_social || {},
    raw_tags: item?.raw_tags || {},
  }
}

// Fonction pour obtenir l'icône selon le type d'activité
const getActivityIcon = (category) => {
  const cat = (category || "").toLowerCase()
  if (cat.includes("restaurant") || cat.includes("cafe") || cat.includes("bar")) {
    return "🍽️"
  }
  if (cat.includes("hotel")) return "🏨"
  if (cat.includes("fuel")) return "⛽"
  if (cat.includes("post_office") || cat.includes("post")) return "📮"
  if (cat.includes("museum")) return "🏛️"
  if (cat.includes("shop") || cat.includes("store")) return "🛍️"
  if (cat.includes("library")) return "📚"
  if (cat.includes("parking")) return "🅿️"
  if (cat.includes("kindergarten") || cat.includes("school")) return "🏫"
  return "📍"
}

// Fonction pour formater les horaires
const formatHoraires = (horaires) => {
  if (!horaires) return null
  // Simplifier l'affichage des horaires complexes
  if (horaires === "24/7") return "Ouvert 24h/24"
  if (horaires.length > 50) {
    return horaires.substring(0, 50) + "..."
  }
  return horaires
}

// Composant pour afficher une carte de résultat
const ResultCard = ({ item, index }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  const hasDetails =
    item.horaires ||
    item.cuisine ||
    item.etoiles ||
    item.operateur ||
    item.marque ||
    Object.keys(item.extras).length > 0 ||
    Object.keys(item.payment).length > 0 ||
    Object.keys(item.raw_tags).length > 0

  return (
    <Card.Root key={item?.entity_key || index} variant="outline" _hover={{ shadow: "sm" }}>
      <Card.Body p="3">
        <VStack align="stretch" gap="2">
          {/* Header compact: Nom + badges + actions sur une ligne */}
          <HStack justify="space-between" align="center" gap="2" flexWrap="wrap">
            <HStack gap="2" flex="1" minW="0">
              <Text fontSize="lg" lineHeight="1">{getActivityIcon(item.category)}</Text>
              <VStack align="start" gap="0" flex="1" minW="0">
                <HStack gap="2" flexWrap="wrap" align="center">
                  <Heading size="sm" fontWeight="700" noOfLines={1}>
                    {item.name}
                  </Heading>
                  <Badge colorPalette="blue" variant="subtle" fontSize="2xs" px="1.5" py="0.5">
                    {item.category}
                  </Badge>
                  {item.marque && (
                    <Badge colorPalette="purple" variant="subtle" fontSize="2xs" px="1.5" py="0.5">
                      {item.marque}
                    </Badge>
                  )}
                  {item.operateur && (
                    <Badge colorPalette="orange" variant="subtle" fontSize="2xs" px="1.5" py="0.5">
                      {item.operateur}
                    </Badge>
                  )}
                  {item.cuisine && (
                    <Badge colorPalette="green" variant="outline" fontSize="2xs" px="1.5" py="0.5">
                      {item.cuisine}
                    </Badge>
                  )}
                  {item.etoiles && (
                    <HStack gap="0.5">
                      <FiStar size="10" color="var(--chakra-colors-yellow-500)" />
                      <Text fontSize="2xs">{item.etoiles}</Text>
                    </HStack>
                  )}
                </HStack>
              </VStack>
            </HStack>
            <HStack gap="1">
              {item.osm && (
                <Tooltip content="Voir sur OpenStreetMap">
                  <Button size="xs" variant="ghost" p="1" as="a" href={item.osm} target="_blank" rel="noreferrer">
                    <FiExternalLink size="14" />
                  </Button>
                </Tooltip>
              )}
              {hasDetails && (
                <Button size="xs" variant="ghost" p="1" onClick={() => setIsExpanded(!isExpanded)}>
                  {isExpanded ? <FiChevronUp size="14" /> : <FiChevronDown size="14" />}
                </Button>
              )}
            </HStack>
          </HStack>

          {/* Ligne 2: Adresse + Horaires */}
          <HStack gap="3" align="start" flexWrap="wrap" fontSize="xs">
            {item.address && item.address !== "-" && (
              <HStack gap="1" flex="1" minW="200px">
                <FiMapPin size="12" color="var(--chakra-colors-fg-muted)" />
                <VStack align="start" gap="0" flex="1" minW="0">
                  <Text fontWeight="500" noOfLines={1}>{item.address}</Text>
                  {(item.city && item.city !== "-") && (
                    <Text color="fg.muted" fontSize="2xs">
                      {item.city}{item.postcode && ` ${item.postcode}`}
                      {item.lat && item.lon && ` • ${item.lat.toFixed(4)}, ${item.lon.toFixed(4)}`}
                    </Text>
                  )}
                </VStack>
              </HStack>
            )}
            {item.horaires && (
              <HStack gap="1" flex="1" minW="150px">
                <FiClock size="12" color="var(--chakra-colors-fg-muted)" />
                <Text noOfLines={1} title={item.horaires}>
                  {formatHoraires(item.horaires)}
                </Text>
              </HStack>
            )}
          </HStack>

          {/* Ligne 3: Contacts compacts */}
          <HStack gap="1.5" flexWrap="wrap" fontSize="xs">
            {item.website && (
              <Tooltip content={item.website}>
                <Button size="xs" variant="outline" colorPalette="blue" px="2" py="1" h="auto" as="a" href={item.website} target="_blank" rel="noreferrer">
                  <FiGlobe size="11" />
                  <Box as="span" ml="1">Web</Box>
                </Button>
              </Tooltip>
            )}
            {item.emails.length > 0 && (
              <Tooltip content={item.emails.join(", ")}>
                <Button size="xs" variant="outline" colorPalette="purple" px="2" py="1" h="auto">
                  <FiMail size="11" />
                  <Box as="span" ml="1">{item.emails.length}</Box>
                </Button>
              </Tooltip>
            )}
            {item.telephones.length > 0 && (
              <Tooltip content={item.telephones.join(", ")}>
                <Button size="xs" variant="outline" colorPalette="green" px="2" py="1" h="auto">
                  <FiPhone size="11" />
                  <Box as="span" ml="1">{item.telephones.length}</Box>
                </Button>
              </Tooltip>
            )}
            {item.whatsapp.length > 0 && (
              <Tooltip content={item.whatsapp.join(", ")}>
                <Button size="xs" variant="outline" colorPalette="green" px="2" py="1" h="auto">
                  <Box as="span" fontSize="2xs">💬</Box>
                  <Box as="span" ml="1">{item.whatsapp.length}</Box>
                </Button>
              </Tooltip>
            )}
          </HStack>

          {/* Détails expandables compacts */}
          {hasDetails && isExpanded && (
            <VStack align="stretch" gap="2" pt="2" mt="2" borderTopWidth="1px" borderColor="border.subtle" fontSize="2xs">
              {/* Payment + Extras + Source sur une ligne */}
              <HStack gap="3" flexWrap="wrap" align="start">
                {Object.keys(item.payment).length > 0 && (
                  <Box>
                    <HStack gap="1" mb="1">
                      <FiCreditCard size="10" />
                      <Text fontWeight="600">Paiement</Text>
                    </HStack>
                    <HStack gap="1" flexWrap="wrap">
                      {Object.entries(item.payment).map(([key, value]) => (
                        <Badge key={key} variant="outline" fontSize="2xs" px="1" py="0.5">
                          {key.replace("payment:", "")}: {String(value)}
                        </Badge>
                      ))}
                    </HStack>
                  </Box>
                )}
                {Object.keys(item.extras).length > 0 && (
                  <Box>
                    <HStack gap="1" mb="1">
                      <FiTag size="10" />
                      <Text fontWeight="600">Extras</Text>
                    </HStack>
                    <HStack gap="1" flexWrap="wrap">
                      {Object.entries(item.extras)
                        .filter(([key]) => !["opening_hours", "cuisine", "brand", "operator"].includes(key))
                        .slice(0, 8)
                        .map(([key, value]) => (
                          <Badge key={key} variant="subtle" colorPalette="gray" fontSize="2xs" px="1" py="0.5">
                            {key}: {String(value).substring(0, 20)}
                          </Badge>
                        ))}
                    </HStack>
                  </Box>
                )}
                {item.source && (
                  <Box>
                    <Text color="fg.muted" mb="1">Source:</Text>
                    <Badge variant="subtle" fontSize="2xs" px="1" py="0.5">{item.source}</Badge>
                  </Box>
                )}
              </HStack>

              {/* Raw tags compacts */}
              {Object.keys(item.raw_tags).length > 0 && (
                <Box>
                  <HStack gap="1" mb="1">
                    <FiTag size="10" />
                    <Text fontWeight="600">Tags OSM ({Object.keys(item.raw_tags).length})</Text>
                  </HStack>
                  <HStack gap="1" flexWrap="wrap">
                    {Object.entries(item.raw_tags)
                      .slice(0, 20)
                      .map(([key, value]) => (
                        <Tooltip key={key} content={`${key} = ${value}`}>
                          <Badge variant="outline" fontSize="2xs" px="1" py="0.5" cursor="help">
                            {key}
                          </Badge>
                        </Tooltip>
                      ))}
                    {Object.keys(item.raw_tags).length > 20 && (
                      <Text fontSize="2xs" color="fg.muted">
                        +{Object.keys(item.raw_tags).length - 20}
                      </Text>
                    )}
                  </HStack>
                </Box>
              )}
            </VStack>
          )}
        </VStack>
      </Card.Body>
    </Card.Root>
  )
}

export default function ResultsTable({ results = [], metadata = {} }) {
  const [searchTerm, setSearchTerm] = useState("")
  const [sortKey, setSortKey] = useState("")
  const [sortDir, setSortDir] = useState("asc")
  const [filterCategory, setFilterCategory] = useState("")

  // Normaliser les résultats
  const normalizedResults = useMemo(() => {
    return Array.isArray(results) ? results.map(normalizeItem) : []
  }, [results])

  // Extraire les catégories uniques pour le filtre
  const categories = useMemo(() => {
    const cats = new Set()
    normalizedResults.forEach((item) => {
      if (item.category && item.category !== "-") {
        cats.add(item.category)
      }
    })
    return Array.from(cats).sort()
  }, [normalizedResults])

  const filteredResults = useMemo(() => {
    let out = [...normalizedResults]

    // Filtrage par catégorie
    if (filterCategory) {
      out = out.filter((item) => item.category === filterCategory)
    }

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
        const marque = (item?.marque || "").toLowerCase()
        const operateur = (item?.operateur || "").toLowerCase()
        const cuisine = (item?.cuisine || "").toLowerCase()
        return (
          name.includes(term) ||
          address.includes(term) ||
          city.includes(term) ||
          category.includes(term) ||
          email.includes(term) ||
          phone.includes(term) ||
          marque.includes(term) ||
          operateur.includes(term) ||
          cuisine.includes(term)
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
  }, [normalizedResults, searchTerm, sortKey, sortDir, filterCategory])

  const exportToExcel = () => {
    // Préparer les données pour Excel
    const excelData = filteredResults.map((item) => ({
      Nom: item.name,
      Adresse: item.address,
      Ville: item.city,
      "Code postal": item.postcode || "",
      Catégorie: item.category,
      "Type catégorie": item.categoryType || "",
      Marque: item.marque || "",
      Opérateur: item.operateur || "",
      Site: item.website || "",
      Email: item.emails.join("; ") || "",
      Téléphone: item.telephones.join("; ") || "",
      WhatsApp: item.whatsapp.join("; ") || "",
      Horaires: item.horaires || "",
      Cuisine: item.cuisine || "",
      Étoiles: item.etoiles || "",
      Latitude: item.lat || "",
      Longitude: item.lon || "",
      "Lien OSM": item.osm || "",
      Source: item.source || "",
      "Tags OSM": JSON.stringify(item.raw_tags),
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
      { wch: 20 }, // Type catégorie
      { wch: 20 }, // Marque
      { wch: 20 }, // Opérateur
      { wch: 30 }, // Site
      { wch: 30 }, // Email
      { wch: 20 }, // Téléphone
      { wch: 20 }, // WhatsApp
      { wch: 40 }, // Horaires
      { wch: 15 }, // Cuisine
      { wch: 10 }, // Étoiles
      { wch: 12 }, // Latitude
      { wch: 12 }, // Longitude
      { wch: 40 }, // Lien OSM
      { wch: 15 }, // Source
      { wch: 50 }, // Tags OSM
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
    <VStack gap="4" align="stretch">
      {/* Header + stats */}
      <Card.Root>
        <Card.Body p="4">
          <VStack gap="3" align="stretch">
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
              <Box display="grid" gridTemplateColumns={{ base: "repeat(2, 1fr)", md: "repeat(4, 1fr)" }} gap="3">
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
                    <Stat.ValueText>{metadata.timings.total_seconds.toFixed(1)}s</Stat.ValueText>
                    <Stat.HelpText>exécution</Stat.HelpText>
                  </Stat.Root>
                )}

                {metadata?.timings?.enrichment?.enabled && (
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
        <Card.Body p="3">
          <VStack gap="2" align="stretch">
            <HStack gap="2" flexWrap="wrap">
              <Box flex="1" minW="220px">
                <Input
                  placeholder="Rechercher dans les résultats…"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </Box>

              <NativeSelect.Root w={{ base: "100%", md: "200px" }}>
                <NativeSelect.Field
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                >
                  <option value="">Toutes les catégories</option>
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </NativeSelect.Field>
              </NativeSelect.Root>

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
                  <option value="marque">Marque</option>
                </NativeSelect.Field>
              </NativeSelect.Root>
            </HStack>

            {(sortKey || filterCategory) && (
              <HStack gap="2" flexWrap="wrap">
                {sortKey && (
                  <Badge colorPalette="blue" variant="subtle">
                    {sortDir === "asc" ? "↑" : "↓"} {sortKey}
                  </Badge>
                )}
                {filterCategory && (
                  <Badge colorPalette="purple" variant="subtle">
                    Catégorie: {filterCategory}
                  </Badge>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setSortKey("")
                    setFilterCategory("")
                    setSearchTerm("")
                  }}
                >
                  Réinitialiser les filtres
                </Button>
              </HStack>
            )}
          </VStack>
        </Card.Body>
      </Card.Root>

      {/* Results Cards */}
      {filteredResults.length === 0 ? (
        <Card.Root>
          <Card.Body>
            <Box py="12" textAlign="center">
              <Text color="fg.muted" fontSize="lg">
                Aucun résultat trouvé
              </Text>
              {(searchTerm || filterCategory) && (
                <Text color="fg.muted" fontSize="sm" mt="2">
                  Essayez de modifier vos critères de recherche
                </Text>
              )}
            </Box>
          </Card.Body>
        </Card.Root>
      ) : (
        <VStack gap="2" align="stretch">
          {filteredResults.map((item, idx) => (
            <ResultCard key={item?.entity_key || idx} item={item} index={idx} />
          ))}
        </VStack>
      )}
    </VStack>
  )
}
