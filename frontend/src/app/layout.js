import { Provider } from "@/components/ui/provider"

export const metadata = {
  title: "My App",
  description: "Next.js + Prisma + Chakra UI v3",
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
