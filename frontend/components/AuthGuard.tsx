'use client'

/**
 * AuthGuard.tsx
 * Wraps protected pages. Redirects to /login if the user is not authenticated.
 * Shows a full-screen spinner while verifying the stored token on mount.
 */
import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Bot } from 'lucide-react'

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!isLoading && !isAuthenticated && pathname !== '/login') {
      router.replace('/login')
    }
  }, [isAuthenticated, isLoading, pathname, router])

  // Show a premium loading screen while the token is being verified
  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface flex flex-col items-center justify-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-900/50 animate-pulse">
          <Bot className="w-7 h-7 text-white" />
        </div>
        <p className="text-sm text-slate-500">Verifying session...</p>
      </div>
    )
  }

  // Don't render the children if the user isn't authenticated yet
  if (!isAuthenticated && pathname !== '/login') {
    return null
  }

  return <>{children}</>
}
