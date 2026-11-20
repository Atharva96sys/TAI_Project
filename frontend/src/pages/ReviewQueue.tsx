import { useEffect, useState } from 'react'
import { api, type AuditEvent } from '../api'
import { ClipboardList, RefreshCw, AlertTriangle, CheckCircle2, Clock } from 'lucide-react'
import { StatusBadge } from '../components/VerificationResult'

export default function ReviewQueue() {
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.listAuditEvents(0, 200)
      .then(evts => {
        // Show only REVIEW or HIGH-risk events
        setEvents(evts.filter(e =>
          e.event_type === 'QUERY_VERIFIED' ||
          e.event_type === 'DOCUMENT_QUARANTINED' ||
          e.event_type === 'SECURITY_THREAT_BLOCKED'
        ))
      })
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const parsePayload = (json: string) => {
    try { return JSON.parse(json) } catch { return {} }
  }

  const reviewItems = events.map(e => {
    const p = parsePayload(e.payload_json)
    const status = p.final_status ?? (e.event_type === 'SECURITY_THREAT_BLOCKED' ? 'BLOCKED' : e.event_type === 'DOCUMENT_QUARANTINED' ? 'BLOCKED' : 'VERIFIED')
    return { ...e, status, payload: p }
  }).filter(e => e.status === 'REVIEW_REQUIRED' || e.status === 'BLOCKED' || e.event_type === 'DOCUMENT_QUARANTINED')

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
            <ClipboardList size={20} color="#a78bfa" />
            <h1 className="page-title">Review Queue</h1>
          </div>
          <p className="page-subtitle">High-risk queries requiring human clinical review, quarantined documents, and blocked threats.</p>
        </div>
        <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} />Refresh</button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.25rem' }}>
        <div className="card stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <AlertTriangle size={16} color="#a78bfa" />
            <span className="stat-label">Awaiting Review</span>
          </div>
          <div className="stat-value" style={{ color: '#a78bfa' }}>{reviewItems.filter(e => e.status === 'REVIEW_REQUIRED').length}</div>
        </div>
        <div className="card stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <AlertTriangle size={16} color="#fb7185" />
            <span className="stat-label">Blocked Threats</span>
          </div>
          <div className="stat-value" style={{ color: '#fb7185' }}>{reviewItems.filter(e => e.status === 'BLOCKED').length}</div>
        </div>
        <div className="card stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <CheckCircle2 size={16} color="#34d399" />
            <span className="stat-label">Total Flagged</span>
          </div>
          <div className="stat-value" style={{ color: '#34d399' }}>{reviewItems.length}</div>
        </div>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Event Type</th>
                <th>Status</th>
                <th>Details</th>
                <th>Actor</th>
                <th>Audit Hash</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#475569' }}><span className="spinner" /></td></tr>
              ) : reviewItems.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#475569' }}>No items currently in review queue.</td></tr>
              ) : reviewItems.slice(0, 50).map(ev => (
                <tr key={ev.id}>
                  <td><code style={{ fontSize: '0.72rem', color: '#22d3ee' }}>{ev.event_type}</code></td>
                  <td><StatusBadge status={ev.status} /></td>
                  <td style={{ maxWidth: 260, fontSize: '0.78rem', color: '#94a3b8' }}>
                    {ev.payload.query_text?.slice(0, 60) ?? ev.payload.document_name ?? JSON.stringify(ev.payload).slice(0, 60)}
                    {(ev.payload.query_text?.length > 60) && '…'}
                  </td>
                  <td style={{ color: '#64748b', fontSize: '0.75rem' }}>{ev.actor_id}</td>
                  <td><code className="hash-chain" style={{ fontSize: '0.65rem' }}>{ev.current_chain_hash.slice(0, 14)}…</code></td>
                  <td style={{ color: '#475569', fontSize: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Clock size={11} />
                      {new Date(ev.created_at).toLocaleString()}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
