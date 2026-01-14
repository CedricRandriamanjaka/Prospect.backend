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
import { FiDownload, FiMail, FiPhone, FiGlobe, FiMapPin } from "react-icons/fi"
import jsPDF from "jspdf"
import autoTable from "jspdf-autotable"
import { Tooltip } from "@/components/ui/tooltip"

export default function ResultsTable({ results = [], metadata = {} }) {
  const [searchTerm, setSearchTerm] = useState("")
  const [sortKey, setSortKey] = useState("")
  const [sortDir, setSortDir] = useState("asc")

  const filteredResults = useMemo(() => {
    let out = Array.isArray(results) ? [...results] : []

    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase()
      out = out.filter((item) => {
        const name = (item?.name || "").toLowerCase()
        const address = (item?.address || "").toLowerCase()
        const city = (item?.city || "").toLowerCase()
        const category = (item?.category || "").toLowerCase()
        return name.includes(term) || address.includes(term) || city.includes(term) || category.includes(term)
      })
    }

    if (sortKey) {
      out.sort((a, b) => {
        const av = (a?.[sortKey] ?? "").toString()
        const bv = (b?.[sortKey] ?? "").toString()
        const cmp = av.localeCompare(bv, undefined, { numeric: true, sensitivity: "base" })
        return sortDir === "asc" ? cmp : -cmp
      })
    }

    return out
  }, [results, searchTerm, sortKey, sortDir])

  const getContactCount = (item) => {
    let c = 0
    if (item?.email) c++
    if (item?.phone) c++
    if (item?.website) c++
    if (item?.whatsapp) c++
    return c
  }

  const exportToPDF = () => {
    const doc = new jsPDF()
    const margin = 14

    doc.setFontSize(18)
    doc.text("Résultats de prospection", margin, 20)

    doc.setFontSize(10)
    let y = 30

    if (metadata?.query) {
      const q = metadata.query?.where || metadata.query?.city || "Coordonnées"
      doc.text(`Recherche: ${q}`, margin, y)
      y += 7
    }

    doc.text(`Nombre de résultats: ${metadata?.count || filteredResults.length}`, margin, y)
    y += 7

    if (metadata?.timings?.total_seconds != null) {
      doc.text(`Temps: ${metadata.timings.total_seconds}s`, margin, y)
      y += 10
    }

    const body = filteredResults.map((item) => [
      item?.name || "-",
      item?.address || "-",
      item?.city || "-",
      item?.category || "-",
      item?.website ? "Oui" : "Non",
      item?.email ? "Oui" : "Non",
      item?.phone ? "Oui" : "Non",
      item?.whatsapp ? "Oui" : "Non",
      getContactCount(item),
    ])

    autoTable(doc, {
      head: [["Nom", "Adresse", "Ville", "Catégorie", "Site", "Email", "Téléphone", "WhatsApp", "Contacts"]],
      body,
      startY: y,
      margin: { left: margin, right: margin },
      styles: { fontSize: 8 },
    })

    doc.save(`prospects-${new Date().toISOString().split("T")[0]}.pdf`)
  }

  const onChangeSort = (val) => {
    if (!val) {
      setSortKey("")
      setSortDir("asc")
      return
    }
    if (val === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortKey(val)
      setSortDir("asc")
    }
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

              <Button colorPalette="blue" onClick={exportToPDF}>
                <FiDownload />
                <Box as="span" ml="2">
                  Export PDF
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
                onChange={(e) => onChangeSort(e.target.value)}
              >
                <option value="">Trier par…</option>
                <option value="name">Nom</option>
                <option value="city">Ville</option>
                <option value="category">Catégorie</option>
                <option value="contacts_count">Contacts</option>
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
                  <Table.ColumnHeader>Nom</Table.ColumnHeader>
                  <Table.ColumnHeader>Adresse</Table.ColumnHeader>
                  <Table.ColumnHeader>Ville</Table.ColumnHeader>
                  <Table.ColumnHeader>Catégorie</Table.ColumnHeader>
                  <Table.ColumnHeader>Contacts</Table.ColumnHeader>
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
                    <Table.Row key={idx}>
                      <Table.Cell fontWeight="700">{item?.name || "-"}</Table.Cell>

                      <Table.Cell>
                        <VStack align="start" gap="1">
                          {item?.address ? (
                            <HStack gap="2">
                              <FiMapPin size="12" />
                              <Text fontSize="sm">{item.address}</Text>
                            </HStack>
                          ) : (
                            <Text fontSize="sm" color="fg.muted">
                              -
                            </Text>
                          )}
                          {item?.postcode ? (
                            <Text fontSize="xs" color="fg.muted">
                              {item.postcode}
                            </Text>
                          ) : null}
                        </VStack>
                      </Table.Cell>

                      <Table.Cell>{item?.city || "-"}</Table.Cell>

                      <Table.Cell>
                        {item?.category ? (
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
                                <Badge variant="outline" colorPalette="blue">
                                  <FiGlobe size="10" />
                                </Badge>
                              </Tooltip>
                            ) : null}

                            {item?.email ? (
                              <Tooltip content={item.email}>
                                <Badge variant="outline" colorPalette="purple">
                                  <FiMail size="10" />
                                </Badge>
                              </Tooltip>
                            ) : null}

                            {item?.phone ? (
                              <Tooltip content={item.phone}>
                                <Badge variant="outline" colorPalette="green">
                                  <FiPhone size="10" />
                                </Badge>
                              </Tooltip>
                            ) : null}

                            {item?.whatsapp ? (
                              <Tooltip content={item.whatsapp}>
                                <Badge variant="outline" colorPalette="green">
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

                          {item?.email ? (
                            <Text fontSize="xs" color="fg.muted">
                              {item.email}
                            </Text>
                          ) : null}

                          {item?.phone ? (
                            <Text fontSize="xs" color="fg.muted">
                              {item.phone}
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
