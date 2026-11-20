import { useEffect, useState } from 'react'
import { api, type SecurityEvent, type SecurityStats } from '../api'
import { Shield, ShieldAlert, ShieldCheck, RefreshCw, Zap } from 'lucide-react'

export default function SecurityCenter() {
  const [events, setEvents] = useState<SecurityEvent[]>([])
  const [stats, setStats] = useState<SecurityStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [testQuery, setTestQuery] = useState('')
  const [scanResult, setScanResult] = useState<any>(null)
  const [scanning, setScanning] = useState(false)

  const load = () => {
    setLoading(true)
    Promise.all([
      api.listSecurityEvents(0, 50),
      api.getSecurityStats(),
    ]).then(([evts, st]) => { setEvents(evts); setStats(st) })
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const runScan = async () => {
    if (!testQuery.trim()) return
    setScanning(true)
    setScanResult(null)
    try { setScanResult(await api.scanQuery(testQuery)) }
    catch (e: any) { setScanResult({ error: e.message }) }
    finally { setScanning(false) }
  }

  const threatColor = (lvl: string) => ({ CRITICAL: '#fb7185', HIGH: '#fb923c', MEDIUM: '#fbbf24', LOW: '#22d3ee', INFO: '#94a3b8' })[lvl] ?? '#94a3b8'
  const threatBg   = (lvl: string) => ({ CRITICAL: 'rgba(244,63,94,0.12)', HIGH: 'rgba(249,115,22,0.12)', MEDIUM: 'rgba(251,191,36,0.08)', LOW: 'rgba(34,211,238,0.08)', INFO: 'rgba(148,163,184,0.08)' })[lvl] ?? 'rgba(148,163,184,0.08)'

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
            <Shield size={20} color="#fb7185" />
            <h1 className="page-title">Security Center</h1>
          </div>
          <p className="page-subtitle">Prompt injection defense · Direct & indirect attack interception · Real-time threat telemetry.</p>
        </div>
        <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} />Refresh</button>
      </div>

      {/* Stats */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
          <StatTile label="Total Events" value={stats.total_events} color="#94a3b8" icon={<Shield size={16} color="#94a3b8" />} />
          <StatTile label="Blocked" value={stats.blocked_count} color="#fb7185" icon={<ShieldAlert size={16} color="#fb7185" />} />
          <StatTile label="Quarantined" value={stats.quarantined_count} color="#fb923c" icon={<ShieldAlert size={16} color="#fb923c" />} />
          <StatTile label="Injection Catch Rate" value={`${stats.injection_catch_rate.toFixed(0)}%`} color="#34d399" icon={<ShieldCheck size={16} color="#34d399" />} />
        </div>
      )}

      {/* Live Scan Tester */}
      <div className="card" style={{ padding: '1.25rem', marginBottom: '1.25rem' }}>
        <div className="section-header" style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}><Zap size={11} /> Airlock Live Scanner</div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <input className="input" placeholder="Paste any text to scan for injection attacks…" value={testQuery} onChange={e => setTestQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && runScan()} />
          <button className="btn btn-primary" onClick={runScan} disabled={scanning || !testQuery.trim()}>
            {scanning ? <span className="spinner" /> : <Shield size={14} />}
            {scanning ? 'Scanning…' : 'Scan'}
          </button>
        </div>
        {scanResult && !scanResult.error && (
          <div style={{ marginTop: '0.875rem', background: threatBg(scanResult.threat_level), border: `1px solid ${threatColor(scanResult.threat_level)}44`, borderRadius: '0.5rem', padding: '0.875rem 1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: 700, color: scanResult.is_safe ? '#34d399' : '#fb7185', fontSize: '0.9rem' }}>
                {scanResult.is_safe ? '✓ SAFE — Cleared' : `✕ ${scanResult.action_taken} — ${scanResult.threat_category}`}
              </span>
              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: threatColor(scanResult.threat_level), textTransform: 'uppercase' }}>{scanResult.threat_level}</span>
            </div>
            {scanResult.detected_pattern && <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: 0 }}>Pattern: <code style={{ color: '#fb923c' }}>{scanResult.detected_pattern}</code></p>}
          </div>
        )}
      </div>

      {/* Events table */}
      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Event Type</th><th>Threat Level</th><th>Source</th><th>Pattern Detected</th><th>Action</th><th>Time</th></tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem' }}><span className="spinner" /></td></tr>
              ) : events.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#475569' }}>No security events recorded.</td></tr>
              ) : events.map(e => (
                <tr key={e.id}>
                  <td><code style={{ fontSize: '0.72rem', color: '#22d3ee' }}>{e.event_type}</code></td>
                  <td>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: threatColor(e.threat_level), textTransform: 'uppercase', background: threatBg(e.threat_level), padding: '0.15rem 0.5rem', borderRadius: '9999px' }}>
                      {e.threat_level}
                    </span>
                  </td>
                  <td style={{ color: '#64748b', fontSize: '0.75rem' }}>{e.source_type}</td>
                  <td style={{ maxWidth: 220, fontSize: '0.75rem', color: '#94a3b8' }}>{e.detected_pattern?.slice(0, 60)}</td>
                  <td><span style={{ fontSize: '0.72rem', fontWeight: 600, color: e.action_taken === 'BLOCKED' ? '#fb7185' : e.action_taken === 'QUARANTINED' ? '#fb923c' : '#34d399', textTransform: 'uppercase' }}>{e.action_taken}</span></td>
                  <td style={{ fontSize: '0.72rem', color: '#475569' }}>{new Date(e.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function StatTile({ label, value, color, icon }: { label: string; value: string | number; color: string; icon: React.ReactNode }) {
  return (
    <div className="card stat-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>{icon}<span className="stat-label">{label}</span></div>
      <div className="stat-value" style={{ color }}>{value}</div>
    </div>
  )
}
