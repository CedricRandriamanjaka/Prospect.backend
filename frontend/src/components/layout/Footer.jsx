"use client"

import { Box, Container, Text, HStack, Link } from "@chakra-ui/react"

export default function Footer() {
  return (
    <Box
      borderTopWidth="1px"
      borderColor="chakra-border-color"
      mt="20"
      bg="surface"
      color="text.secondary"
    >
      <Container maxW="7xl" py="6">
        <HStack justify="space-between" align="center" flexWrap="wrap" gap="4">
          <Text fontSize="sm" color="text.muted">
            © {new Date().getFullYear()} Prospect. Tous droits réservés.
          </Text>
          <Text fontSize="sm" color="text.muted">
            Développé par{" "}
            <Link
              href="https://rcedric.netlify.app"
              target="_blank"
              rel="noopener noreferrer"
              color="blue.500"
              _hover={{ color: "blue.600", textDecoration: "underline" }}
              _dark={{ color: "blue.400", _hover: { color: "blue.300" } }}
              fontWeight="500"
            >
              Cedric Randriamanjaka
            </Link>
          </Text>
        </HStack>
      </Container>
    </Box>
  )
}
