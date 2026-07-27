'use client'

import { useCallback, useEffect, useState } from 'react'
import {
  MessageSquare, RefreshCw, AlertCircle, CheckCircle,
  ChevronDown, ChevronUp, Filter
} from 'lucide-react'
import { api, type NudgeLog, type Drive } from '@/lib/api'
import { format, formatDistanceToNow } from 'date-fns'

const LEVEL_CONFIG = {
  1: { label: 'Polite',  cls: 'badge-sent',    color: 'text-blue-400' },
  2: { label: 'Urgent',  cls: 'badge-pending',  color: 'text-amber-400' },
  3: { label: 'FOMO',    cls: 'badge-failed',   color: 'text-red-400' },
}

export default function LogsPage() {
  const [logs, setLogs] = useState<NudgeLog[]>([])
  const [drives, setDrives] = useState<Drive[]>([])
  const [loading, setLoading] = useState(true)
  const [filterDrive, setFilterDrive] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    try {
      const [l, d] = await Promise.all([
        api.logs(filterDrive ? { drive_id: filterDrive } : undefined),
        api.drives.list(),
      ])
      setLogs(l)
      setDrives(d)
    } finally {
      setLoading(false)
    }
  }, [filterDrive])

  useEffect(() => { fetchLogs() }, [fetchLogs])

  const sent = logs.filter(l => l.status === 'sent').length
  const failed = logs.filter(l => l.status === 'failed').length

  return (
    <div className="flex-1 p-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Nudge Logs</h1>
          <p className="text-sm text-slate-500 mt-1">
            {logs.length} messages · {sent} sent · {failed} failed
          </p>
        </div>
        <button onClick={fetchLogs} className="btn-secondary btn-sm" disabled={loading}>
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total Sent',  value: logs.length, color: 'text-slate-200' },
          { label: 'Delivered',   value: sent,        color: 'text-emerald-400' },
          { label: 'Failed',      value: failed,      color: 'text-red-400' },
          { label: 'Unique Students', value: new Set(logs.map(l => l.student_id)).size, color: 'text-brand-400' },
        ].map(item => (
          <div key={item.label} className="card p-4 flex flex-col gap-1">
            <p className={`text-2xl font-bold ${item.color}`}>{item.value}</p>
            <p className="text-xs text-slate-500">{item.label}</p>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="flex gap-3">
        <select
          value={filterDrive}
          onChange={e => setFilterDrive(e.target.value)}
          className="input w-48"
        >
          <option value="">All Drives</option>
          {drives.map(d => <option key={d.id} value={d.id}>{d.company_name}</option>)}
        </select>
      </div>

      {/* Logs Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b border-surface-border bg-surface/50">
              <tr>
                <th className="th">Student</th>
                <th className="th">Drive</th>
                <th className="th">Level</th>
                <th className="th">Status</th>
                <th className="th">Sent At</th>
                <th className="th">Message Preview</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="table-row">
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="td">
                        <div className="h-4 bg-surface-border rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-slate-600">
                    <MessageSquare className="w-8 h-8 mx-auto mb-3 opacity-30" />
                    <p>No nudge logs yet. Trigger a nudge from the dashboard.</p>
                  </td>
                </tr>
              ) : (
                logs.map(log => {
                  const lvl = LEVEL_CONFIG[log.nudge_level as 1 | 2 | 3] || LEVEL_CONFIG[1]
                  const drive = drives.find(d => d.id === log.drive_id)
                  const isExpanded = expandedId === log.id
                  return (
                    <>
                      <tr
                        key={log.id}
                        className="table-row cursor-pointer"
                        onClick={() => setExpandedId(isExpanded ? null : log.id)}
                      >
                        <td className="td">
                          <div>
                            <p className="font-medium text-slate-200">
                              {log.student?.name || 'Unknown'}
                            </p>
                            <p className="text-xs text-slate-500">
                              {log.student?.roll_number}
                            </p>
                          </div>
                        </td>
                        <td className="td">
                          <span className="text-xs text-slate-400">{drive?.company_name || '—'}</span>
                        </td>
                        <td className="td">
                          <span className={`badge ${lvl.cls}`}>
                            L{log.nudge_level} · {lvl.label}
                          </span>
                        </td>
                        <td className="td">
                          {log.status === 'sent' ? (
                            <span className="flex items-center gap-1.5 text-emerald-400 text-xs">
                              <CheckCircle className="w-3.5 h-3.5" /> Sent
                            </span>
                          ) : (
                            <span className="flex items-center gap-1.5 text-red-400 text-xs">
                              <AlertCircle className="w-3.5 h-3.5" /> Failed
                            </span>
                          )}
                        </td>
                        <td className="td">
                          <div>
                            <p className="text-xs text-slate-300">
                              {format(new Date(log.sent_at), 'dd MMM yyyy, HH:mm')}
                            </p>
                            <p className="text-xs text-slate-600">
                              {formatDistanceToNow(new Date(log.sent_at), { addSuffix: true })}
                            </p>
                          </div>
                        </td>
                        <td className="td">
                          <p className="text-xs text-slate-400 truncate max-w-[200px]">
                            {log.message_sent.slice(0, 80)}...
                          </p>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-surface/50">
                          <td colSpan={6} className="px-6 py-4">
                            <div className="space-y-2">
                              <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Full Message</p>
                              <pre className="text-sm text-slate-200 whitespace-pre-wrap font-sans leading-relaxed p-4 bg-surface rounded-xl border border-surface-border">
                                {log.message_sent}
                              </pre>
                              {log.error_message && (
                                <p className="text-xs text-red-400 flex items-center gap-2 mt-2">
                                  <AlertCircle className="w-3.5 h-3.5" /> {log.error_message}
                                </p>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
