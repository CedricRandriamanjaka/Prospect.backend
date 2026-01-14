"use client"

import { Box, Container, Text } from "@chakra-ui/react"

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
        <Text fontSize="sm" color="text.muted">
          © {new Date().getFullYear()} Prospect. Tous droits réservés.
        </Text>
      </Container>
    </Box>
  )
}
