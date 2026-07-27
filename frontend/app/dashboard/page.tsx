'use client'

import { useEffect, useState, useCallback } from 'react'
import {
  Users, CheckCircle, Clock, Ban, Send, Wifi,
  Briefcase, RefreshCw, Zap, TrendingUp, AlertCircle
} from 'lucide-react'
import { api, type Stats, type Drive } from '@/lib/api'
import { formatDistanceToNow, format } from 'date-fns'
import UploadZone from '@/components/UploadZone'

function StatCard({
  icon: Icon, label, value, sub, color = 'brand'
}: {
  icon: any; label: string; value: number | string; sub?: string; color?: string
}) {
  const colors: Record<string, string> = {
    brand:   'from-brand-500/20 to-brand-600/5   border-brand-500/30   text-brand-400',
    emerald: 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/30 text-emerald-400',
    amber:   'from-amber-500/20 to-amber-600/5   border-amber-500/30   text-amber-400',
    red:     'from-red-500/20 to-red-600/5       border-red-500/30     text-red-400',
    blue:    'from-blue-500/20 to-blue-600/5     border-blue-500/30    text-blue-400',
    violet:  'from-violet-500/20 to-violet-600/5 border-violet-500/30  text-violet-400',
  }
  const cls = colors[color] || colors.brand

  return (
    <div className={`stat-card bg-gradient-to-br ${cls} border animate-slide-up`}>
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center bg-current/10`}>
        <Icon className={`w-5 h-5 ${cls.split(' ').find(c => c.startsWith('text-'))}`} />
      </div>
      <div className="mt-2">
        <p className="text-2xl font-bold text-slate-100">{value}</p>
        <p className="text-sm font-medium text-slate-400">{label}</p>
        {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

function RegistrationBar({ rate }: { rate: number }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-slate-400">
        <span>Registration Rate</span>
        <span className="font-semibold text-slate-200">{rate}%</span>
      </div>
      <div className="h-2 bg-surface-border rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-brand-500 to-emerald-400 rounded-full transition-all duration-700"
          style={{ width: `${rate}%` }}
        />
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [drives, setDrives] = useState<Drive[]>([])
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [nudgeMsg, setNudgeMsg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [s, d] = await Promise.all([api.stats(), api.drives.list()])
      setStats(s)
      setDrives(d)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const triggerNudge = async () => {
    setTriggering(true)
    setNudgeMsg(null)
    try {
      const res = await api.nudge.trigger()
      setNudgeMsg(res.message)
      setTimeout(() => setNudgeMsg(null), 5000)
    } catch (e: any) {
      setNudgeMsg(`Error: ${e.message}`)
    } finally {
      setTriggering(false)
    }
  }

  return (
    <div className="flex-1 p-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">Placement Compliance Overview</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetchData} className="btn-secondary btn-sm" disabled={loading}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button onClick={triggerNudge} className="btn-primary" disabled={triggering}>
            <Zap className={`w-4 h-4 ${triggering ? 'animate-pulse' : ''}`} />
            {triggering ? 'Sending Nudges...' : 'Trigger Nudge Now'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span className="text-sm">Could not connect to backend: {error}. Make sure FastAPI is running on port 8000.</span>
        </div>
      )}

      {/* Nudge confirmation */}
      {nudgeMsg && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 animate-slide-up">
          <CheckCircle className="w-4 h-4 shrink-0" />
          <span className="text-sm">{nudgeMsg}</span>
        </div>
      )}

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={Users}       label="Total Students"    value={stats.total_students}  color="brand" />
          <StatCard icon={CheckCircle} label="Registered"        value={stats.registered}      color="emerald" sub={`${stats.registration_rate}% rate`} />
          <StatCard icon={Clock}       label="Pending"           value={stats.pending}         color="amber" />
          <StatCard icon={Ban}         label="Blocked"           value={stats.blocked}         color="red" />
          <StatCard icon={Wifi}        label="Linked to Telegram" value={stats.with_telegram}  color="blue" />
          <StatCard icon={Briefcase}   label="Active Drives"     value={stats.active_drives}   color="violet" />
          <StatCard icon={Send}        label="Nudges Today"      value={stats.nudges_today}    color="brand" />
          <StatCard icon={TrendingUp}  label="Total Nudges Sent" value={stats.nudges_total}    color="brand" />
        </div>
      )}

      {/* Registration Progress */}
      {stats && (
        <div className="card p-6 animate-slide-up">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Registration Progress</h2>
          <RegistrationBar rate={stats.registration_rate} />
          <div className="flex gap-6 mt-4 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-brand-500" />
              Registered ({stats.registered})
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              Pending ({stats.pending})
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              Blocked ({stats.blocked})
            </span>
          </div>
        </div>
      )}

      {/* Two-column layout */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Quick Upload */}
        <div className="card p-6 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300">Quick CSV Upload</h2>
          <UploadZone drives={drives} onSuccess={fetchData} compact />
        </div>

        {/* Active Drives */}
        <div className="card p-6 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300">Active Drives</h2>
          {drives.filter(d => d.is_active).length === 0 ? (
            <div className="text-center py-8 text-slate-600">
              <Briefcase className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No active drives. Create one in the Drives page.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {drives.filter(d => d.is_active).slice(0, 5).map(drive => (
                <div key={drive.id} className="flex items-center justify-between p-3 rounded-xl bg-surface border border-surface-border hover:border-surface-muted transition-colors">
                  <div>
                    <p className="text-sm font-medium text-slate-200">{drive.company_name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Deadline: {format(new Date(drive.deadline), 'dd MMM yyyy, hh:mm a')}
                    </p>
                  </div>
                  <span className="text-xs text-emerald-400 font-medium">
                    {formatDistanceToNow(new Date(drive.deadline), { addSuffix: true })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
