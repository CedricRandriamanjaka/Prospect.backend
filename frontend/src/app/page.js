"use client"

import NextLink from "next/link"
import {
  Box,
  Button,
  Container,
  Heading,
  HStack,
  SimpleGrid,
  Stack,
  Text,
  VStack,
  Icon,
  Badge,
  Flex,
} from "@chakra-ui/react"
import { FiSearch, FiMapPin, FiMail, FiPhone, FiGlobe, FiZap, FiTrendingUp, FiShield } from "react-icons/fi"
import Navbar from "@/components/layout/Navbar"
import Footer from "@/components/layout/Footer"

function Feature({ icon, title, desc, color }) {
  return (
    <VStack
      align="flex-start"
      p="8"
      borderWidth="1px"
      borderColor="chakra-border-color"
      rounded="xl"
      bg="surface"
      spacing="4"
      _hover={{
        borderColor: color || "accent",
        transform: "translateY(-4px)",
        transition: "all 0.3s ease",
        boxShadow: "lg",
      }}
      transition="all 0.3s ease"
    >
      <Box
        p="3"
        rounded="lg"
        bg={color ? `${color}.50` : "accent.50"}
        color={color || "accent"}
        _dark={{
          bg: color ? `${color}.950` : "accent.950",
          color: color || "accent.400",
        }}
      >
        <Icon boxSize="6" as={icon} />
      </Box>
      <Heading size="md" color="text.primary" fontWeight="700">
        {title}
      </Heading>
      <Text color="text.secondary" fontSize="sm" lineHeight="1.7">
        {desc}
      </Text>
    </VStack>
  )
}

function Stat({ value, label }) {
  return (
    <VStack spacing="1">
      <Text fontSize="3xl" fontWeight="800" color="accent" lineHeight="1">
        {value}
      </Text>
      <Text fontSize="sm" color="text.secondary" fontWeight="500">
        {label}
      </Text>
    </VStack>
  )
}

export default function HomePage() {
  return (
    <Box minH="100vh" bg="chakra-body-bg" color="text.primary" position="relative" overflow="hidden">
      {/* Gradient background effects */}
      <Box
        position="absolute"
        top="-20%"
        right="-10%"
        w="600px"
        h="600px"
        bg="accent.500"
        opacity="0.1"
        rounded="full"
        filter="blur(100px)"
        _dark={{ opacity: 0.05 }}
      />
      <Box
        position="absolute"
        bottom="-20%"
        left="-10%"
        w="500px"
        h="500px"
        bg="brand.500"
        opacity="0.1"
        rounded="full"
        filter="blur(100px)"
        _dark={{ opacity: 0.05 }}
      />

      <Navbar />

      <Container maxW="7xl" py={{ base: "12", md: "24" }} position="relative" zIndex="1">
        {/* Hero Section */}
        <Stack gap="8" textAlign={{ base: "left", md: "center" }} maxW="4xl" mx="auto" mb="20">
          <Badge
            px="3"
            py="1"
            rounded="full"
            bg="accent.50"
            color="accent.700"
            fontSize="xs"
            fontWeight="600"
            letterSpacing="0.05em"
            textTransform="uppercase"
            w="fit-content"
            mx={{ base: "0", md: "auto" }}
            _dark={{ bg: "accent.950", color: "accent.300" }}
          >
            🚀 La prospection réinventée
          </Badge>

          <Heading
            size={{ base: "3xl", md: "5xl" }}
            color="text.primary"
            fontWeight="900"
            letterSpacing="-0.04em"
            lineHeight="1.1"
          >
            Trouvez vos prospects
            <br />
            <Box as="span" color="accent" position="relative">
              en quelques clics
              <Box
                as="span"
                position="absolute"
                bottom="0"
                left="0"
                right="0"
                h="20%"
                bg="accent.200"
                opacity="0.3"
                _dark={{ bg: "accent.800", opacity: 0.4 }}
              />
            </Box>
          </Heading>

          <Text
            fontSize={{ base: "lg", md: "xl" }}
            color="text.secondary"
            lineHeight="1.8"
            maxW="2xl"
            mx="auto"
            fontWeight="400"
          >
            Prospect.com est l'outil de prospection le plus puissant et intuitif. Recherchez par localisation,
            enrichissez automatiquement vos contacts, et boostez votre business avec des données précises et à jour.
          </Text>

          <HStack justify={{ base: "flex-start", md: "center" }} gap="4" pt="4" flexWrap="wrap">
            <Button
              as={NextLink}
              href="/prospect"
              size="xl"
              bg="text.primary"
              color="surface"
              fontWeight="600"
              px="10"
              py="7"
              fontSize="lg"
              rounded="xl"
              _hover={{
                opacity: 0.9,
                transform: "translateY(-2px)",
                boxShadow: "xl",
              }}
              transition="all 0.2s"
            >
              Commencer la prospection
            </Button>
            <Button
              as={NextLink}
              href="/auth/login"
              variant="outline"
              size="xl"
              colorPalette="neutral"
              fontWeight="600"
              px="10"
              py="7"
              fontSize="lg"
              rounded="xl"
              borderWidth="2px"
              borderColor="chakra-border-color"
              _hover={{
                borderColor: "accent",
                color: "accent",
                transform: "translateY(-2px)",
              }}
              transition="all 0.2s"
            >
              Se connecter
            </Button>
          </HStack>

          {/* Stats */}
          <Flex
            justify={{ base: "flex-start", md: "center" }}
            gap={{ base: "6", md: "12" }}
            pt="8"
            flexWrap="wrap"
          >
            <Stat value="10K+" label="Prospects trouvés" />
            <Stat value="95%" label="Taux de précision" />
            <Stat value="24/7" label="Disponibilité" />
          </Flex>
        </Stack>

        {/* Features Grid */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap="6" mt="20">
          <Feature
            icon={FiSearch}
            title="Recherche intelligente"
            desc="Recherchez par texte libre, coordonnées GPS, ou utilisez notre carte interactive. Filtrez par secteur, tags OSM, et bien plus encore."
            color="accent"
          />
          <Feature
            icon={FiMapPin}
            title="Géolocalisation précise"
            desc="Trouvez des prospects dans un rayon personnalisable. Recherche par ville, quartier, adresse ou cliquez directement sur la carte."
            color="blue"
          />
          <Feature
            icon={FiZap}
            title="Enrichissement automatique"
            desc="Récupérez automatiquement emails, téléphones, sites web et WhatsApp de vos prospects. Données vérifiées et à jour."
            color="purple"
          />
          <Feature
            icon={FiMail}
            title="Contacts complets"
            desc="Accédez à tous les moyens de contact : emails professionnels, numéros de téléphone, et liens WhatsApp pour un contact direct."
            color="green"
          />
          <Feature
            icon={FiTrendingUp}
            title="Filtres avancés"
            desc="Excluez des marques, filtrez par nombre de contacts, triez par pertinence, distance ou aléatoirement. Contrôle total."
            color="orange"
          />
          <Feature
            icon={FiShield}
            title="Données sécurisées"
            desc="Vos recherches et résultats sont protégés. Exportez en PDF, manipulez les données, tout en gardant le contrôle."
            color="red"
          />
        </SimpleGrid>

        {/* CTA Section */}
        <Box
          mt="24"
          p="12"
          rounded="2xl"
          bg="surface"
          borderWidth="1px"
          borderColor="chakra-border-color"
          textAlign="center"
        >
          <VStack spacing="6">
            <Heading size="xl" color="text.primary" fontWeight="800">
              Prêt à transformer votre prospection ?
            </Heading>
            <Text fontSize="lg" color="text.secondary" maxW="2xl">
              Rejoignez des milliers d'entreprises qui utilisent Prospect.com pour trouver et contacter leurs
              prospects.
            </Text>
            <Button
              as={NextLink}
              href="/prospect"
              size="xl"
              bg="text.primary"
              color="surface"
              fontWeight="600"
              px="10"
              py="7"
              fontSize="lg"
              rounded="xl"
              _hover={{
                opacity: 0.9,
                transform: "translateY(-2px)",
                boxShadow: "xl",
              }}
              transition="all 0.2s"
            >
              Démarrer maintenant
            </Button>
          </VStack>
        </Box>
      </Container>

      <Footer />
    </Box>
  )
}
