import { createSystem, defaultConfig } from "@chakra-ui/react"

// Palette de couleurs moderne style Lovable - Noir/Blanc/Gris pour outil de prospection
export const colors = {
  // Couleur principale (brand) - Noir profond avec accent subtil
  brand: {
    50: "#fafafa",
    100: "#f5f5f5",
    200: "#e5e5e5",
    300: "#d4d4d4",
    400: "#a3a3a3",
    500: "#737373", // Gris moyen
    600: "#525252",
    700: "#404040",
    800: "#262626", // Noir doux
    900: "#171717", // Noir profond
    950: "#0a0a0a", // Noir pur
  },
  // Couleur accent - Bleu subtil et professionnel
  accent: {
    50: "#f0f9ff",
    100: "#e0f2fe",
    200: "#bae6fd",
    300: "#7dd3fc",
    400: "#38bdf8",
    500: "#0ea5e9", // Bleu moderne
    600: "#0284c7",
    700: "#0369a1",
    800: "#075985",
    900: "#0c4a6e",
    950: "#082f49",
  },
  // Gris neutres pour l'interface
  neutral: {
    50: "#fafafa",
    100: "#f5f5f5",
    200: "#e5e5e5",
    300: "#d4d4d4",
    400: "#a3a3a3",
    500: "#737373",
    600: "#525252",
    700: "#404040",
    800: "#262626",
    900: "#171717",
    950: "#0a0a0a",
  },
}

// Configuration du système de thème personnalisé - Style Lovable moderne
export const customSystem = createSystem(defaultConfig, {
  theme: {
    tokens: {
      colors: {
        // Couleurs brand (noir/gris) personnalisées
        "brand.50": { value: colors.brand[50] },
        "brand.100": { value: colors.brand[100] },
        "brand.200": { value: colors.brand[200] },
        "brand.300": { value: colors.brand[300] },
        "brand.400": { value: colors.brand[400] },
        "brand.500": { value: colors.brand[500] },
        "brand.600": { value: colors.brand[600] },
        "brand.700": { value: colors.brand[700] },
        "brand.800": { value: colors.brand[800] },
        "brand.900": { value: colors.brand[900] },
        "brand.950": { value: colors.brand[950] },

        // Couleurs accent (bleu subtil) personnalisées
        "accent.50": { value: colors.accent[50] },
        "accent.100": { value: colors.accent[100] },
        "accent.200": { value: colors.accent[200] },
        "accent.300": { value: colors.accent[300] },
        "accent.400": { value: colors.accent[400] },
        "accent.500": { value: colors.accent[500] },
        "accent.600": { value: colors.accent[600] },
        "accent.700": { value: colors.accent[700] },
        "accent.800": { value: colors.accent[800] },
        "accent.900": { value: colors.accent[900] },
        "accent.950": { value: colors.accent[950] },

        // Couleurs neutres
        "neutral.50": { value: colors.neutral[50] },
        "neutral.100": { value: colors.neutral[100] },
        "neutral.200": { value: colors.neutral[200] },
        "neutral.300": { value: colors.neutral[300] },
        "neutral.400": { value: colors.neutral[400] },
        "neutral.500": { value: colors.neutral[500] },
        "neutral.600": { value: colors.neutral[600] },
        "neutral.700": { value: colors.neutral[700] },
        "neutral.800": { value: colors.neutral[800] },
        "neutral.900": { value: colors.neutral[900] },
        "neutral.950": { value: colors.neutral[950] },
      },
    },
    semanticTokens: {
      colors: {
        // Couleurs de base - Mode clair (fond blanc, texte noir)
        "chakra-body-bg": {
          value: {
            _light: "#ffffff",
            _dark: "#0a0a0a",
          },
        },
        "chakra-body-text": {
          value: {
            _light: "#171717",
            _dark: "#fafafa",
          },
        },
        "chakra-border-color": {
          value: {
            _light: "#e5e5e5",
            _dark: "#262626",
          },
        },
        // Couleur principale (noir/gris) avec support dark mode
        primary: {
          value: {
            _light: "{colors.brand.900}",
            _dark: "{colors.brand.100}",
          },
        },
        "primary.solid": {
          value: {
            _light: "{colors.brand.950}",
            _dark: "{colors.brand.50}",
          },
        },
        "primary.subtle": {
          value: {
            _light: "{colors.brand.50}",
            _dark: "{colors.brand.900}",
          },
        },
        // Couleur accent (bleu) avec support dark mode
        accent: {
          value: {
            _light: "{colors.accent.500}",
            _dark: "{colors.accent.400}",
          },
        },
        "accent.solid": {
          value: {
            _light: "{colors.accent.600}",
            _dark: "{colors.accent.500}",
          },
        },
        // Couleurs pour les surfaces et cartes
        surface: {
          value: {
            _light: "#ffffff",
            _dark: "#171717",
          },
        },
        "surface.subtle": {
          value: {
            _light: "#fafafa",
            _dark: "#262626",
          },
        },
        // Couleurs pour le texte
        "text.primary": {
          value: {
            _light: "#171717",
            _dark: "#fafafa",
          },
        },
        "text.secondary": {
          value: {
            _light: "#737373",
            _dark: "#a3a3a3",
          },
        },
        "text.muted": {
          value: {
            _light: "#a3a3a3",
            _dark: "#525252",
          },
        },
      },
    },
  },
})
