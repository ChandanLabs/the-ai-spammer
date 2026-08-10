import type { Metadata } from 'next'
import './globals.css'
import Sidebar from '@/components/Sidebar'
import AuthGuard from '@/components/AuthGuard'

export const metadata: Metadata = {
  title: 'PlacementBot Admin — Nudge & Compliance Dashboard',
  description: 'Manage student placement drives, upload CSVs, and automate Telegram nudge campaigns.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen flex bg-surface">
        <AuthGuard>
          <Sidebar />
          <main className="flex-1 flex flex-col min-h-screen overflow-auto">
            {children}
          </main>
        </AuthGuard>
      </body>
    </html>
  )
}
