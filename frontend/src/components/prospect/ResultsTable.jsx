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
  Input,
  NativeSelect,
  Tooltip,
  Flex,
  SimpleGrid,
  Card,
  Stat,
  Table,
  useToast,
} from "@chakra-ui/react"
import { FiDownload, FiMail, FiPhone, FiGlobe, FiMapPin } from "react-icons/fi"
import jsPDF from "jspdf"
import autoTable from "jspdf-autotable"

export default function ResultsTable({ results, metadata }) {
  const [searchTerm, setSearchTerm] = useState("")
  const [sortConfig, setSortConfig] = useState({ key: "", direction: "asc" })
  const toast = useToast()

  const filteredResults = useMemo(() => {
    let filtered = [...(results || [])]

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter((item) => {
        return (
          item.name?.toLowerCase().includes(term) ||
          item.address?.toLowerCase().includes(term) ||
          item.city?.toLowerCase().includes(term) ||
          item.category?.toLowerCase().includes(term)
        )
      })
    }

    if (sortConfig.key) {
      filtered.sort((a, b) => {
        const aVal = a?.[sortConfig.key] ?? ""
        const bVal = b?.[sortConfig.key] ?? ""
        const cmp = aVal.toString().localeCompare(bVal.toString())
        return sortConfig.direction === "asc" ? cmp : -cmp
      })
    }

    return filtered
  }, [results, searchTerm, sortConfig])

  const handleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "asc" ? "desc" : "asc",
    }))
  }

  const getContactCount = (item) => {
    let count = 0
    if (item.email) count++
    if (item.phone) count++
    if (item.website) count++
    if (item.whatsapp) count++
    return count
  }

  const exportToPDF = () => {
    try {
      const doc = new jsPDF()
      const margin = 14

      doc.setFontSize(18)
      doc.text("Résultats de prospection", margin, 20)

      doc.setFontSize(10)
      let yPos = 30
      if (metadata?.query) {
        doc.text(
          `Recherche: ${metadata.query.where || metadata.query.city || "Coordonnées"}`,
          margin,
          yPos
        )
        yPos += 7
      }
      doc.text(`Nombre de résultats: ${metadata?.count || filteredResults.length}`, margin, yPos)
      yPos += 7
      if (metadata?.timings?.total_seconds) {
        doc.text(`Temps d'exécution: ${metadata.timings.total_seconds}s`, margin, yPos)
        yPos += 10
      }

      const tableData = filteredResults.map((item) => [
        item.name || "-",
        item.address || "-",
        item.city || "-",
        item.category || "-",
        item.website ? "Oui" : "Non",
        item.email ? "Oui" : "Non",
        item.phone ? "Oui" : "Non",
        item.whatsapp ? "Oui" : "Non",
        item.contacts_count || getContactCount(item) || 0,
      ])

      autoTable(doc, {
        head: [["Nom", "Adresse", "Ville", "Catégorie", "Site web", "Email", "Téléphone", "WhatsApp", "Contacts"]],
        body: tableData,
        startY: yPos,
        margin: { left: margin, right: margin },
        styles: { fontSize: 8 },
      })

      doc.save(`prospects-${new Date().toISOString().split("T")[0]}.pdf`)

      toast({
        title: "Export réussi",
        description: "Le fichier PDF a été téléchargé",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
    } catch (error) {
      toast({
        title: "Erreur d'export",
        description: error?.message || "Erreur inconnue",
        status: "error",
        duration: 5000,
        isClosable: true,
      })
    }
  }

  return (
    <VStack gap="6" align="stretch">
      {/* Stats */}
      <Card.Root>
        <Card.Body>
          <VStack gap="6" align="stretch">
            <Flex justify="space-between" align="center" flexWrap="wrap" gap="4">
              <Heading size="lg" fontWeight="800">
                Résultats de la prospection
              </Heading>
              <Button colorPalette="blue" onClick={exportToPDF} fontWeight="600">
                <FiDownload />
                Exporter en PDF
              </Button>
            </Flex>

            <SimpleGrid columns={{ base: 2, md: 4 }} gap="4">
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

              {metadata?.timings?.total_seconds ? (
                <Stat.Root>
                  <Stat.Label>Temps</Stat.Label>
                  <Stat.ValueText>{metadata.timings.total_seconds}s</Stat.ValueText>
                  <Stat.HelpText>d'exécution</Stat.HelpText>
                </Stat.Root>
              ) : null}

              {metadata?.enrich_max > 0 ? (
                <Stat.Root>
                  <Stat.Label>Enrichis</Stat.Label>
                  <Stat.ValueText>{metadata?.timings?.enrichment?.enriched_count || 0}</Stat.ValueText>
                  <Stat.HelpText>prospects</Stat.HelpText>
                </Stat.Root>
              ) : null}
            </SimpleGrid>
          </VStack>
        </Card.Body>
      </Card.Root>

      {/* Recherche + tri */}
      <Card.Root>
        <Card.Body>
          <HStack gap="4" flexWrap="wrap">
            <Box flex="1" minW="200px">
              <Input
                placeholder="Rechercher dans les résultats..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </Box>

            <Box maxW="220px" w="100%">
              <NativeSelect.Root>
                <NativeSelect.Field
                  value={sortConfig.key}
                  onChange={(e) => {
                    const key = e.target.value
                    if (!key) return setSortConfig({ key: "", direction: "asc" })
                    handleSort(key)
                  }}
                >
                  <option value="">Trier par…</option>
                  <option value="name">Nom</option>
                  <option value="city">Ville</option>
                  <option value="category">Catégorie</option>
                  <option value="contacts_count">Contacts</option>
                </NativeSelect.Field>
                <NativeSelect.Indicator />
              </NativeSelect.Root>
            </Box>
          </HStack>
        </Card.Body>
      </Card.Root>

      {/* Tableau */}
      <Card.Root>
        <Card.Body p="0">
          <Box overflowX="auto">
            <Table.Root size="sm">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader
                    cursor="pointer"
                    onClick={() => handleSort("name")}
                  >
                    Nom {sortConfig.key === "name" ? (sortConfig.direction === "asc" ? "↑" : "↓") : ""}
                  </Table.ColumnHeader>

                  <Table.ColumnHeader>Adresse</Table.ColumnHeader>

                  <Table.ColumnHeader
                    cursor="pointer"
                    onClick={() => handleSort("city")}
                  >
                    Ville {sortConfig.key === "city" ? (sortConfig.direction === "asc" ? "↑" : "↓") : ""}
                  </Table.ColumnHeader>

                  <Table.ColumnHeader>Catégorie</Table.ColumnHeader>
                  <Table.ColumnHeader>Contacts</Table.ColumnHeader>
                  <Table.ColumnHeader>Détails</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>

              <Table.Body>
                {filteredResults.length === 0 ? (
                  <Table.Row>
                    <Table.Cell colSpan={6} textAlign="center" py="8">
                      <Text color="fg.muted">Aucun résultat trouvé</Text>
                    </Table.Cell>
                  </Table.Row>
                ) : (
                  filteredResults.map((item, index) => (
                    <Table.Row key={index} _hover={{ bg: "bg.subtle" }}>
                      <Table.Cell fontWeight="600">{item.name || "-"}</Table.Cell>

                      <Table.Cell>
                        <VStack align="flex-start" gap="1">
                          {item.address ? (
                            <HStack gap="1">
                              <FiMapPin size="12" />
                              <Text fontSize="sm">{item.address}</Text>
                            </HStack>
                          ) : null}
                          {item.postcode ? (
                            <Text fontSize="xs" color="fg.muted">
                              {item.postcode}
                            </Text>
                          ) : null}
                        </VStack>
                      </Table.Cell>

                      <Table.Cell>{item.city || "-"}</Table.Cell>

                      <Table.Cell>
                        {item.category ? (
                          <Badge colorPalette="cyan" variant="subtle">
                            {item.category}
                          </Badge>
                        ) : null}
                      </Table.Cell>

                      <Table.Cell>
                        <VStack align="flex-start" gap="1">
                          <Badge colorPalette="green" variant="solid">
                            {getContactCount(item)} contact{getContactCount(item) > 1 ? "s" : ""}
                          </Badge>

                          <HStack gap="2" flexWrap="wrap">
                            {item.website ? (
                              <Tooltip content={item.website}>
                                <Badge colorPalette="blue" variant="outline">
                                  <FiGlobe size="10" />
                                </Badge>
                              </Tooltip>
                            ) : null}

                            {item.email ? (
                              <Tooltip content={item.email}>
                                <Badge colorPalette="purple" variant="outline">
                                  <FiMail size="10" />
                                </Badge>
                              </Tooltip>
                            ) : null}

                            {item.phone ? (
                              <Tooltip content={item.phone}>
                                <Badge colorPalette="green" variant="outline">
                                  <FiPhone size="10" />
                                </Badge>
                              </Tooltip>
                            ) : null}

                            {item.whatsapp ? (
                              <Tooltip content={item.whatsapp}>
                                <Badge colorPalette="green" variant="outline">
                                  WhatsApp
                                </Badge>
                              </Tooltip>
                            ) : null}
                          </HStack>
                        </VStack>
                      </Table.Cell>

                      <Table.Cell>
                        <VStack align="flex-start" gap="1">
                          {item.website ? (
                            <Text
                              fontSize="xs"
                              color="cyan.fg"
                              as="a"
                              href={item.website}
                              target="_blank"
                              rel="noreferrer"
                            >
                              {item.website}
                            </Text>
                          ) : null}

                          {item.email ? <Text fontSize="xs">{item.email}</Text> : null}
                          {item.phone ? <Text fontSize="xs">{item.phone}</Text> : null}

                          {typeof item.distance === "number" ? (
                            <Text fontSize="xs" color="fg.muted">
                              {item.distance.toFixed(2)} km
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
