// src/components/ui/switch.jsx
"use client"

import { Switch as ChakraSwitch } from "@chakra-ui/react"

export function Switch({ checked, onCheckedChange, label, ...props }) {
  return (
    <ChakraSwitch.Root
      checked={checked}
      onCheckedChange={(e) => onCheckedChange?.(e.checked)}
      {...props}
    >
      <ChakraSwitch.HiddenInput />
      <ChakraSwitch.Control />
      {label ? <ChakraSwitch.Label>{label}</ChakraSwitch.Label> : null}
    </ChakraSwitch.Root>
  )
}
