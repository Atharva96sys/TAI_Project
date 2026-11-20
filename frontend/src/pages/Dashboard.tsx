import { useEffect, useState } from 'react'
import { api, type GovernanceMetrics } from '../api'
import { Activity, Shield, Lock, FileText, BarChart3, CheckCircle2, AlertTriangle, Clock } from 'lucide-react'

export default function Dashboard() {
  const [metrics, setMetrics] = useState<GovernanceMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getGovernanceMetrics()
      .then(setMetrics)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingState />
  if (error)   return <ErrorState message={error} />

  const m = metrics!
  const total = m.total_queries || 1
  const verifiedPct  = ((m.verified_count / total) * 100).toFixed(1)
  const reviewPct    = ((m.review_required_count / total) * 100).toFixed(1)

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="page-title">Clinical Operations Dashboard</h1>
        <p className="page-subtitle">Real-time telemetry · NIST AI RMF 1.0 · EU AI Act aligned</p>
      </div>

      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        <StatCard icon={<Activity size={18} color="#34d399" />} label="Total Queries" value={m.total_queries} glow="#34d399" />
        <StatCard icon={<CheckCircle2 size={18} color="#34d399" />} label="Verified" value={`${verifiedPct}%`} glow="#34d399" />
        <StatCard icon={<Shield size={18} color="#fb7185" />} label="Blocked Threats" value={m.blocked_count} glow="#fb7185" />
        <StatCard icon={<Clock size={18} color="#a78bfa" />} label="Mean Latency" value={`${m.mean_latency_ms.toFixed(0)}ms`} glow="#a78bfa" />
      </div>

      {/* Second KPI row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        <StatCard icon={<FileText size={18} color="#22d3ee" />} label="Clinical Docs" value={m.total_documents} glow="#22d3ee" />
        <StatCard icon={<AlertTriangle size={18} color="#fb923c" />} label="Quarantined" value={m.quarantined_documents} glow="#fb923c" />
        <StatCard icon={<BarChart3 size={18} color="#fbbf24" />} label="Under Review" value={`${reviewPct}%`} glow="#fbbf24" />
        <StatCard icon={<Lock size={18} color="#34d399" />} label="Audit Chain" value={m.audit_chain_valid ? 'Intact' : 'Alert'} glow={m.audit_chain_valid ? '#34d399' : '#fb7185'} />
      </div>

      {/* 2-col layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.25rem' }}>

        {/* Evidence Coverage */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div className="section-header">Evidence & Grounding Quality</div>
          <MetricRow label="Mean Evidence Coverage" value={`${m.mean_evidence_coverage.toFixed(1)}%`} pct={m.mean_evidence_coverage} />
          <MetricRow label="Mean Grounding Accuracy" value={`${m.mean_grounding_accuracy.toFixed(1)}%`} pct={m.mean_grounding_accuracy} />
        </div>

        {/* Query Status Distribution */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div className="section-header">Query Status Distribution</div>
          <StatusRow label="Verified" count={m.verified_count} total={total} color="#34d399" />
          <StatusRow label="Partially Verified" count={m.partial_count} total={total} color="#fbbf24" />
          <StatusRow label="Insufficient Evidence" count={m.insufficient_count} total={total} color="#94a3b8" />
          <StatusRow label="Contradictory" count={m.contradictory_count} total={total} color="#fb923c" />
          <StatusRow label="Blocked" count={m.blocked_count} total={total} color="#fb7185" />
          <StatusRow label="Review Required" count={m.review_required_count} total={total} color="#a78bfa" />
        </div>
      </div>

      {/* NIST AI RMF Controls */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <div className="section-header">NIST AI RMF 1.0 Control Status</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.625rem' }}>
          {Object.entries(m.nist_controls).map(([id, ctrl]) => (
            <div key={id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0.75rem', background: 'rgba(15,23,42,0.4)', borderRadius: '0.5rem', border: '1px solid rgba(148,163,184,0.08)' }}>
              <div>
                <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#cbd5e1' }}>{id}</div>
                <div style={{ fontSize: '0.7rem', color: '#475569' }}>{ctrl.description}</div>
              </div>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: ctrl.status === 'COMPLIANT' ? '#34d399' : '#fbbf24', textTransform: 'uppercase' }}>{ctrl.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, glow }: { icon: React.ReactNode; label: string; value: string | number; glow: string }) {
  return (
    <div className="card stat-card" style={{ borderColor: `${glow}22` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        {icon}
        <span className="stat-label">{label}</span>
      </div>
      <div className="stat-value" style={{ color: glow }}>{value}</div>
    </div>
  )
}

function MetricRow({ label, value, pct }: { label: string; value: string; pct: number }) {
  const color = pct >= 85 ? '#34d399' : pct >= 60 ? '#fbbf24' : '#fb7185'
  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
        <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>{label}</span>
        <span style={{ fontSize: '0.82rem', fontWeight: 600, color }}>{value}</span>
      </div>
      <div className="progress-bar-wrap">
        <div className="progress-bar-fill" style={{ width: `${Math.min(100, pct)}%`, background: `linear-gradient(90deg,${color}66,${color})` }} />
      </div>
    </div>
  )
}

function StatusRow({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = (count / total) * 100
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.5rem' }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
      <span style={{ fontSize: '0.8rem', color: '#94a3b8', flex: 1 }}>{label}</span>
      <div className="progress-bar-wrap" style={{ width: 80 }}>
        <div className="progress-bar-fill" style={{ width: `${Math.min(100, pct)}%`, background: color }} />
      </div>
      <span style={{ fontSize: '0.78rem', fontWeight: 600, color, minWidth: 24, textAlign: 'right' }}>{count}</span>
    </div>
  )
}

function LoadingState() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 300, gap: '1rem' }}>
      <div className="spinner" style={{ width: 32, height: 32 }} />
      <p style={{ color: '#475569', fontSize: '0.85rem' }}>Loading dashboard telemetry…</p>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 300, gap: '0.5rem' }}>
      <AlertTriangle size={32} color="#fb7185" />
      <p style={{ color: '#fb7185', fontSize: '0.85rem' }}>Backend unreachable — start the FastAPI server</p>
      <p style={{ color: '#475569', fontSize: '0.75rem', fontFamily: 'monospace' }}>{message}</p>
    </div>
  )
}
