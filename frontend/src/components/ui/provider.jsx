"use client"

import { ChakraProvider } from "@chakra-ui/react"
import { ThemeProvider } from "next-themes"
import { customSystem } from "@/theme"

export function Provider({ children }) {
  return (
    <ChakraProvider value={customSystem}>
      <ThemeProvider attribute="class" disableTransitionOnChange defaultTheme="light">
        {children}
      </ThemeProvider>
    </ChakraProvider>
  )
}
