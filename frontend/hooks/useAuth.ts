'use client'

/**
 * useAuth.ts — Lightweight auth hook
 * Stores the JWT token in localStorage and provides:
 *   - login(username, password)  → calls /api/auth/login, stores token
 *   - logout()                   → clears token
 *   - token                      → raw JWT string (or null)
 *   - isAuthenticated            → boolean
 *   - isLoading                  → true while verifying on mount
 */
import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'

const TOKEN_KEY = 'placement_admin_token'
const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useAuth() {
  const router = useRouter()
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // On mount, read stored token and verify it's still valid with the server
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY)
    if (!stored) {
      setIsLoading(false)
      return
    }

    // Verify token with backend
    fetch(`${BASE}/api/auth/verify`, {
      headers: { Authorization: `Bearer ${stored}` },
    })
      .then(async (res) => {
        if (res.ok) {
          setToken(stored)
        } else {
          // Token expired or invalid — clear it
          localStorage.removeItem(TOKEN_KEY)
        }
      })
      .catch(() => {
        // Network error — keep the stored token optimistically
        setToken(stored)
      })
      .finally(() => setIsLoading(false))
  }, [])

  const login = useCallback(
    async (username: string, password: string): Promise<void> => {
      const res = await fetch(`${BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Login failed' }))
        throw new Error(err.detail || 'Invalid credentials')
      }

      const data = await res.json()
      localStorage.setItem(TOKEN_KEY, data.access_token)
      setToken(data.access_token)
      router.push('/dashboard')
    },
    [router]
  )

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    router.push('/login')
  }, [router])

  return {
    token,
    isAuthenticated: !!token,
    isLoading,
    login,
    logout,
  }
}
