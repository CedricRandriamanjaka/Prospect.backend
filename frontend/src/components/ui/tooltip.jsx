// src/components/ui/tooltip.jsx
"use client"

import { Tooltip as ChakraTooltip } from "@chakra-ui/react"

export function Tooltip({ content, children, openDelay = 250, ...props }) {
  if (!content) return <>{children}</>

  return (
    <ChakraTooltip.Root openDelay={openDelay} {...props}>
      <ChakraTooltip.Trigger asChild>{children}</ChakraTooltip.Trigger>
      <ChakraTooltip.Positioner>
        <ChakraTooltip.Content>
          {content}
          <ChakraTooltip.Arrow />
        </ChakraTooltip.Content>
      </ChakraTooltip.Positioner>
    </ChakraTooltip.Root>
  )
}
