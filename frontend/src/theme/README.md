# Configuration du Thème Chakra UI - Style Lovable

Ce projet utilise un thème moderne noir/blanc/gris inspiré de Lovable, optimisé pour un outil de prospection B2B professionnel.

## Palette de couleurs

### Couleur principale (Brand) - Noir/Gris
- **Couleur principale** : Noir profond (`brand.900` = `#171717`)
- **Gris moyen** : `brand.500` = `#737373`
- Palette complète de 50 (clair) à 950 (noir pur)
- Utilisez `colorPalette="brand"` pour les boutons principaux

### Couleur accent - Bleu moderne
- **Couleur accent** : Bleu (`accent.500` = `#0ea5e9`)
- Utilisé pour les liens, focus, et éléments interactifs
- Utilisez `colorPalette="accent"` ou `color="accent"`

### Couleurs sémantiques (recommandées)

#### Fond et surfaces
- `chakra-body-bg` : Fond principal (blanc/noir selon mode)
- `surface` : Fond des cartes et conteneurs
- `surface.subtle` : Fond subtil pour les zones secondaires

#### Texte
- `text.primary` : Texte principal (noir/blanc selon mode)
- `text.secondary` : Texte secondaire (gris)
- `text.muted` : Texte discret (gris clair)

#### Bordures
- `chakra-border-color` : Bordures (gris clair/sombre selon mode)

#### Couleurs interactives
- `primary` : Couleur principale (noir/blanc selon mode)
- `accent` : Couleur accent (bleu, s'adapte au dark mode)

## Utilisation recommandée

### Boutons

```jsx
// Bouton principal (noir)
<Button bg="text.primary" color="surface">
  Action principale
</Button>

// Bouton secondaire (outline)
<Button variant="outline" borderColor="chakra-border-color">
  Action secondaire
</Button>

// Bouton avec accent
<Button colorPalette="accent">
  Action accent
</Button>
```

### Textes

```jsx
// Texte principal
<Text color="text.primary">Titre important</Text>

// Texte secondaire
<Text color="text.secondary">Description</Text>

// Texte discret
<Text color="text.muted">Note ou hint</Text>
```

### Conteneurs et cartes

```jsx
// Carte principale
<Box bg="surface" borderColor="chakra-border-color" borderWidth="1px">
  Contenu
</Box>

// Zone subtile
<Box bg="surface.subtle">
  Contenu secondaire
</Box>
```

### Liens et éléments interactifs

```jsx
// Lien avec accent
<Link color="accent" _hover={{ textDecoration: "underline" }}>
  Lien
</Link>

// Input avec focus accent
<Input
  borderColor="chakra-border-color"
  _focus={{ borderColor: "accent" }}
/>
```

## Dark Mode

Le dark mode est géré automatiquement via `next-themes`. Toutes les couleurs sémantiques s'adaptent automatiquement :
- Mode clair : Fond blanc, texte noir
- Mode sombre : Fond noir (`#0a0a0a`), texte blanc

Utilisez le bouton `ColorModeButton` dans la Navbar pour basculer.

## Design System

### Principes
- **Minimalisme** : Design épuré, beaucoup d'espace blanc
- **Contraste élevé** : Noir/blanc pour une excellente lisibilité
- **Accents subtils** : Bleu utilisé avec parcimonie pour les éléments interactifs
- **Typographie** : Letter-spacing négatif pour les titres (`-0.03em`)

### Espacements
- Utilisez des espacements généreux (gap="6", py="12")
- Containers max-width : `7xl` pour le contenu principal

## Personnalisation

Pour modifier les couleurs, éditez `src/theme/index.js` :

1. Modifiez les valeurs dans l'objet `colors`
2. Ajustez les `semanticTokens` pour les couleurs sémantiques
3. Les changements s'appliquent automatiquement dans toute l'application
