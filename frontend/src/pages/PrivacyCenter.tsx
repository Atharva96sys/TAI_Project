import { useEffect, useState } from 'react'
import { api, type PrivacyEvent, type PrivacyStats } from '../api'
import { Lock, RefreshCw, Eye, EyeOff } from 'lucide-react'

export default function PrivacyCenter() {
  const [events, setEvents] = useState<PrivacyEvent[]>([])
  const [stats, setStats] = useState<PrivacyStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [testText, setTestText] = useState('')
  const [scanResult, setScanResult] = useState<any>(null)
  const [scanning, setScanning] = useState(false)
  const [showTokenMap, setShowTokenMap] = useState(false)

  const load = () => {
    setLoading(true)
    Promise.all([api.listPrivacyEvents(0, 50), api.getPrivacyStats()])
      .then(([evts, st]) => { setEvents(evts); setStats(st) })
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const runScan = async () => {
    if (!testText.trim()) return
    setScanning(true); setScanResult(null)
    try { setScanResult(await api.scanText(testText)) }
    catch (e: any) { setScanResult({ error: e.message }) }
    finally { setScanning(false) }
  }

  const entityColor = (t: string) => ({ NAME: '#a78bfa', MRN: '#22d3ee', EMAIL: '#34d399', PHONE: '#fbbf24', SSN: '#fb7185', DOB: '#fb923c' })[t] ?? '#94a3b8'

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
            <Lock size={20} color="#22d3ee" />
            <h1 className="page-title">Privacy Center</h1>
          </div>
          <p className="page-subtitle">HIPAA 18-identifier detection, reversible pseudonymization, and PII event audit log.</p>
        </div>
        <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} />Refresh</button>
      </div>

      {/* Stats */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
          <div className="card stat-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}><Lock size={16} color="#22d3ee" /><span className="stat-label">Total PII Events</span></div>
            <div className="stat-value" style={{ color: '#22d3ee' }}>{stats.total_events}</div>
          </div>
          <div className="card stat-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}><Eye size={16} color="#34d399" /><span className="stat-label">PII Recall Rate</span></div>
            <div className="stat-value" style={{ color: '#34d399' }}>{stats.pii_catch_rate.toFixed(0)}%</div>
          </div>
          <div className="card stat-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}><EyeOff size={16} color="#a78bfa" /><span className="stat-label">Entity Types</span></div>
            <div className="stat-value" style={{ color: '#a78bfa' }}>{Object.keys(stats.entity_type_breakdown).length}</div>
          </div>
        </div>
      )}

      {/* Entity Breakdown */}
      {stats && Object.keys(stats.entity_type_breakdown).length > 0 && (
        <div className="card" style={{ padding: '1.25rem', marginBottom: '1.25rem' }}>
          <div className="section-header">HIPAA 18 Identifier Type Breakdown</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {Object.entries(stats.entity_type_breakdown).map(([type, count]) => (
              <div key={type} style={{ background: 'rgba(15,23,42,0.6)', border: `1px solid ${entityColor(type)}33`, borderRadius: '0.5rem', padding: '0.5rem 0.875rem', textAlign: 'center' }}>
                <div style={{ fontSize: '0.65rem', fontWeight: 700, color: entityColor(type), textTransform: 'uppercase', letterSpacing: '0.06em' }}>{type}</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#e2e8f0' }}>{count}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Live Scanner */}
      <div className="card" style={{ padding: '1.25rem', marginBottom: '1.25rem' }}>
        <div className="section-header">Privacy Shield — Live PII Scanner</div>
        <textarea
          className="input"
          rows={3}
          placeholder="Paste clinical text to scan for HIPAA identifiers… (e.g. 'Patient Jane Doe, MRN-112233, DOB 1975-04-12')"
          value={testText}
          onChange={e => setTestText(e.target.value)}
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.625rem' }}>
          <button className="btn btn-primary" onClick={runScan} disabled={scanning || !testText.trim()}>
            {scanning ? <span className="spinner" /> : <Lock size={14} />}
            {scanning ? 'Scanning…' : 'Scan for PII'}
          </button>
        </div>

        {scanResult && !scanResult.error && (
          <div style={{ marginTop: '0.875rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: 600, color: scanResult.has_pii ? '#fbbf24' : '#34d399', fontSize: '0.85rem' }}>
                {scanResult.has_pii ? `⚠ ${scanResult.total_redactions} PII identifiers detected & pseudonymized` : '✓ No HIPAA identifiers detected'}
              </span>
              {scanResult.has_pii && (
                <button className="btn btn-ghost" style={{ fontSize: '0.72rem', padding: '0.2rem 0.5rem' }} onClick={() => setShowTokenMap(!showTokenMap)}>
                  {showTokenMap ? <EyeOff size={12} /> : <Eye size={12} />}{showTokenMap ? 'Hide Map' : 'Show Token Map'}
                </button>
              )}
            </div>
            <div className="evidence-block"><pre style={{ margin: 0, fontSize: '0.82rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{scanResult.protected_text}</pre></div>
            {showTokenMap && scanResult.has_pii && (
              <div style={{ marginTop: '0.625rem', display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                {Object.entries(scanResult.token_map as Record<string, string>).map(([tok, orig]) => (
                  <div key={tok} style={{ background: 'rgba(34,211,238,0.08)', border: '1px solid rgba(34,211,238,0.2)', borderRadius: '0.375rem', padding: '0.25rem 0.5rem', fontSize: '0.72rem' }}>
                    <code style={{ color: '#22d3ee' }}>{tok}</code><span style={{ color: '#475569' }}> → </span><code style={{ color: '#94a3b8' }}>{orig}</code>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Events table */}
      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Entity Type</th><th>Masked Snippet</th><th>Token</th><th>Source</th><th>Time</th></tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', padding: '2rem' }}><span className="spinner" /></td></tr>
              ) : events.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: '#475569' }}>No PII redaction events recorded.</td></tr>
              ) : events.map(e => (
                <tr key={e.id}>
                  <td><span style={{ fontSize: '0.72rem', fontWeight: 700, color: entityColor(e.entity_type), textTransform: 'uppercase' }}>{e.entity_type}</span></td>
                  <td style={{ fontSize: '0.75rem', color: '#94a3b8', maxWidth: 240 }}>{e.masked_snippet}</td>
                  <td><code style={{ fontSize: '0.72rem', color: '#22d3ee' }}>{e.redacted_token}</code></td>
                  <td style={{ color: '#64748b', fontSize: '0.75rem' }}>{e.source_type}</td>
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
