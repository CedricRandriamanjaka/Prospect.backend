"use client"

import NextLink from "next/link"
import { Box, Container, Flex, HStack, Link, Button, Text } from "@chakra-ui/react"
import { ColorModeButton } from "@/components/ui/color-mode-button"

export default function Navbar() {
  return (
    <Box
      borderBottomWidth="1px"
      borderColor="chakra-border-color"
      bg="surface"
      color="text.primary"
    >
      <Container maxW="7xl" py="4">
        <Flex align="center" justify="space-between">
          <Text
            fontWeight="700"
            fontSize="xl"
            letterSpacing="-0.02em"
            color="text.primary"
          >
            Prospect
          </Text>
          <HStack gap="4">
            <Link
              as={NextLink}
              href="/"
              color="text.secondary"
              fontSize="sm"
              fontWeight="500"
              _hover={{ color: "text.primary" }}
              transition="color 0.2s"
            >
              Accueil
            </Link>
            <Button
              as={NextLink}
              href="/auth/login"
              variant="ghost"
              size="sm"
              colorPalette="neutral"
              fontWeight="500"
            >
              Connexion
            </Button>
            <Button
              as={NextLink}
              href="/auth/register"
              size="sm"
              colorPalette="brand"
              bg="text.primary"
              color="surface"
              fontWeight="500"
              _hover={{ opacity: 0.9 }}
            >
              Inscription
            </Button>
            <ColorModeButton />
          </HStack>
        </Flex>
      </Container>
    </Box>
  )
}
