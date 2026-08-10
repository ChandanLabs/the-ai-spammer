// lib/api.ts — typed API client with JWT auth

const TOKEN_KEY = 'placement_admin_token'
const BASE = '/api/admin'

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { ...init, headers })

  if (res.status === 401) {
    // Token expired — clear it and redirect to login
    localStorage.removeItem(TOKEN_KEY)
    if (typeof window !== 'undefined') window.location.href = '/login'
    throw new Error('Session expired. Please log in again.')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}


// ── Types ─────────────────────────────────────────────────────────────────────

export type StudentStatus = 'PENDING' | 'REGISTERED' | 'BLOCKED'

export interface Drive {
  id: string
  company_name: string
  registration_link: string | null
  deadline: string
  is_active: boolean
  created_at: string
}

export interface Student {
  id: string
  name: string
  roll_number: string
  email: string | null
  branch: string | null
  year: string | null
  phone: string | null
  telegram_chat_id: number | null
  status: StudentStatus
  nudge_count: number
  last_nudge_sent_at: string | null
  drive_id: string | null
  created_at: string
}

export interface NudgeLog {
  id: string
  student_id: string
  drive_id: string
  message_sent: string
  nudge_level: number
  sent_at: string
  status: 'sent' | 'failed'
  error_message: string | null
  student?: Student
}

export interface Stats {
  total_students: number
  registered: number
  pending: number
  blocked: number
  with_telegram: number
  active_drives: number
  nudges_today: number
  nudges_total: number
  registration_rate: number
}

export interface UploadResult {
  total_rows: number
  inserted: number
  updated: number
  skipped: number
  errors: string[]
}

// ── API functions ─────────────────────────────────────────────────────────────

export const api = {
  stats: () => req<Stats>('/stats'),

  drives: {
    list: () => req<Drive[]>('/drives'),
    create: (d: Omit<Drive, 'id' | 'created_at'>) =>
      req<Drive>('/drives', { method: 'POST', body: JSON.stringify(d) }),
    update: (id: string, d: Partial<Drive>) =>
      req<Drive>(`/drives/${id}`, { method: 'PATCH', body: JSON.stringify(d) }),
    delete: (id: string) => req<void>(`/drives/${id}`, { method: 'DELETE' }),
  },

  students: {
    list: (params?: { drive_id?: string; status?: StudentStatus; search?: string }) => {
      const qs = new URLSearchParams()
      if (params?.drive_id) qs.set('drive_id', params.drive_id)
      if (params?.status)   qs.set('status', params.status)
      if (params?.search)   qs.set('search', params.search)
      return req<Student[]>(`/students?${qs}`)
    },
    update: (id: string, d: { status?: StudentStatus; drive_id?: string }) =>
      req<Student>(`/students/${id}`, { method: 'PATCH', body: JSON.stringify(d) }),
  },

  upload: async (file: File, drive_id?: string): Promise<UploadResult> => {
    const fd = new FormData()
    fd.append('file', file)
    const qs = drive_id ? `?drive_id=${drive_id}` : ''
    const token = getToken()
    const res = await fetch(`${BASE}/upload-csv${qs}`, {
      method: 'POST',
      body: fd,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (res.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      if (typeof window !== 'undefined') window.location.href = '/login'
      throw new Error('Session expired.')
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    return res.json()
  },

  logs: (params?: { drive_id?: string; student_id?: string }) => {
    const qs = new URLSearchParams()
    if (params?.drive_id)   qs.set('drive_id', params.drive_id)
    if (params?.student_id) qs.set('student_id', params.student_id)
    return req<NudgeLog[]>(`/logs?${qs}`)
  },

  nudge: {
    trigger: () => req<{ status: string; message: string }>('/nudge/trigger', { method: 'POST' }),
  },
}
