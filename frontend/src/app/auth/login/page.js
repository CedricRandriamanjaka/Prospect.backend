"use client"

import NextLink from "next/link"
import {
  Box,
  Button,
  Container,
  Heading,
  Input,
  Link,
  Stack,
  Text,
} from "@chakra-ui/react"
import Navbar from "@/components/layout/Navbar"
import Footer from "@/components/layout/Footer"

export default function LoginPage() {
  function onSubmit(e) {
    e.preventDefault()
    alert("Login (placeholder) — aucune logique pour l'instant.")
  }

  return (
    <Box minH="100vh" bg="chakra-body-bg" color="text.primary">
      <Navbar />
      <Container maxW="md" py="12">
        <Box
          borderWidth="1px"
          borderColor="chakra-border-color"
          rounded="lg"
          p="8"
          bg="surface"
        >
          <Stack gap="6">
            <Box>
              <Heading size="lg" color="text.primary" fontWeight="600">
                Connexion
              </Heading>
              <Text color="text.secondary" fontSize="sm" mt="2">
                Accédez à votre compte pour gérer vos prospects.
              </Text>
            </Box>

            <form onSubmit={onSubmit}>
              <Stack gap="4">
                <Box>
                  <Text mb="2" color="text.primary" fontSize="sm" fontWeight="500">
                    Email
                  </Text>
                  <Input
                    type="email"
                    placeholder="name@email.com"
                    bg="surface"
                    borderColor="chakra-border-color"
                    color="text.primary"
                    _focus={{ borderColor: "accent", boxShadow: "none" }}
                    _placeholder={{ color: "text.muted" }}
                  />
                </Box>

                <Box>
                  <Text mb="2" color="text.primary" fontSize="sm" fontWeight="500">
                    Mot de passe
                  </Text>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    bg="surface"
                    borderColor="chakra-border-color"
                    color="text.primary"
                    _focus={{ borderColor: "accent", boxShadow: "none" }}
                    _placeholder={{ color: "text.muted" }}
                  />
                </Box>

                <Button
                  type="submit"
                  w="full"
                  bg="text.primary"
                  color="surface"
                  fontWeight="500"
                  _hover={{ opacity: 0.9 }}
                  mt="2"
                >
                  Se connecter
                </Button>
              </Stack>
            </form>

            <Text fontSize="sm" color="text.secondary" textAlign="center">
              Pas de compte ?{" "}
              <Link
                as={NextLink}
                href="/auth/register"
                color="accent"
                fontWeight="500"
                _hover={{ textDecoration: "underline" }}
              >
                Créer un compte
              </Link>
            </Text>
          </Stack>
        </Box>
      </Container>
      <Footer />
    </Box>
  )
}
