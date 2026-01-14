"use client"

import { IconButton } from "@chakra-ui/react"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"
import { LuMoon, LuSun } from "react-icons/lu"

export function ColorModeButton() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  const isDark = theme === "dark"

  return (
    <IconButton
      onClick={() => setTheme(isDark ? "light" : "dark")}
      variant="ghost"
      aria-label={isDark ? "Passer en mode clair" : "Passer en mode sombre"}
      size="sm"
    >
      {isDark ? <LuSun /> : <LuMoon />}
    </IconButton>
  )
}
