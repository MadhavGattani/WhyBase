import './globals.css'
import type { ReactNode } from 'react'

export const metadata = {
  title: 'Loominal',
  description: 'Loominal — AI assistant demo',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
