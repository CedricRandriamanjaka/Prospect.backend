import { Provider } from "@/components/ui/provider"
import "./globals.css"

export const metadata = {
  title: "Prospect.com - Prospection intelligente",
  description: "Trouvez et enrichissez vos prospects avec un outil moderne et puissant",
}

export default function RootLayout({ children }) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body>
        <Provider>{children}</Provider>
      </body>
    </html>
  )
}
