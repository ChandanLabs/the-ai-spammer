'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard, Users, Briefcase, MessageSquare,
  Bot, Zap, ChevronRight, LogOut
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

const nav = [
  { href: '/dashboard',  icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/students',   icon: Users,            label: 'Students' },
  { href: '/drives',     icon: Briefcase,        label: 'Drives' },
  { href: '/logs',       icon: MessageSquare,    label: 'Nudge Logs' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const { logout, isAuthenticated } = useAuth()

  // Don't render the sidebar on the login page
  if (pathname === '/login') return null

  return (
    <aside className="w-64 min-h-screen bg-surface-card border-r border-surface-border flex flex-col shrink-0">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-surface-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-900/50">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-bold text-slate-100 text-sm leading-none">PlacementBot</p>
            <p className="text-xs text-slate-500 mt-0.5">Admin Console</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, icon: Icon, label }) => {
          const active = pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium
                transition-all duration-200 group
                ${active
                  ? 'bg-brand-600/20 text-brand-400 border border-brand-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'}
              `}
            >
              <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-brand-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
              {label}
              {active && <ChevronRight className="w-3 h-3 ml-auto text-brand-400" />}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-surface-border space-y-3">
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-slow" />
          <span className="text-xs text-emerald-400 font-medium">Bot Active</span>
          <Zap className="w-3 h-3 text-emerald-400 ml-auto" />
        </div>

        {isAuthenticated && (
          <button
            id="sidebar-logout"
            onClick={logout}
            className="btn-danger w-full justify-center btn-sm"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        )}
        <p className="text-xs text-slate-600 text-center">v2.0.0 — Placement Nudge</p>
      </div>
    </aside>
  )
}

