"use client"

import NextLink from "next/link"
import { Box, Button, Container, Heading, HStack, SimpleGrid, Stack, Text } from "@chakra-ui/react"
import Navbar from "@/components/layout/Navbar"
import Footer from "@/components/layout/Footer"

function Feature({ title, desc }) {
  return (
    <Box
      borderWidth="1px"
      borderColor="chakra-border-color"
      rounded="lg"
      p="6"
      bg="surface"
      _hover={{
        borderColor: "accent",
        transform: "translateY(-2px)",
        transition: "all 0.2s ease",
        boxShadow: "sm",
      }}
    >
      <Heading size="md" mb="2" color="text.primary" fontWeight="600">
        {title}
      </Heading>
      <Text color="text.secondary" fontSize="sm" lineHeight="1.6">
        {desc}
      </Text>
    </Box>
  )
}

export default function HomePage() {
  return (
    <Box minH="100vh" bg="chakra-body-bg" color="text.primary">
      <Navbar />

      <Container maxW="7xl" py={{ base: "12", md: "24" }}>
        <Stack gap="8" textAlign={{ base: "left", md: "center" }} maxW="3xl" mx="auto">
          <Heading
            size={{ base: "3xl", md: "4xl" }}
            color="text.primary"
            fontWeight="700"
            letterSpacing="-0.03em"
            lineHeight="1.1"
          >
            Prospection moderne
            <br />
            <Box as="span" color="accent">
              simplifiée
            </Box>
          </Heading>
          <Text
            fontSize={{ base: "lg", md: "xl" }}
            color="text.secondary"
            lineHeight="1.6"
            maxW="2xl"
            mx="auto"
          >
            Trouvez et enrichissez vos prospects avec un outil moderne et puissant.
            Prêt pour la production.
          </Text>

          <HStack justify={{ base: "flex-start", md: "center" }} gap="3" pt="2">
            <Button
              as={NextLink}
              href="/auth/register"
              size="lg"
              bg="text.primary"
              color="surface"
              fontWeight="500"
              px="8"
              _hover={{ opacity: 0.9 }}
            >
              Commencer gratuitement
            </Button>
            <Button
              as={NextLink}
              href="/auth/login"
              variant="outline"
              size="lg"
              colorPalette="neutral"
              fontWeight="500"
              px="8"
              borderColor="chakra-border-color"
            >
              Se connecter
            </Button>
          </HStack>
        </Stack>

        <SimpleGrid columns={{ base: 1, md: 3 }} gap="6" mt="16">
          <Feature
            title="Recherche intelligente"
            desc="Trouvez des prospects par localisation, secteur d'activité et critères avancés."
          />
          <Feature
            title="Enrichissement automatique"
            desc="Récupérez automatiquement emails, téléphones et sites web de vos prospects."
          />
          <Feature
            title="Interface moderne"
            desc="Design épuré et intuitif pour une expérience utilisateur optimale."
          />
        </SimpleGrid>
      </Container>

      <Footer />
    </Box>
  )
}
