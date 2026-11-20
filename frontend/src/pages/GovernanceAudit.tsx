import { useEffect, useState } from 'react'
import { api, type AuditEvent, type AuditChainVerification } from '../api'
import { BarChart3, RefreshCw, CheckCircle2, XCircle, Download } from 'lucide-react'

export default function GovernanceAudit() {
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [chain, setChain]   = useState<AuditChainVerification | null>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    Promise.all([api.listAuditEvents(0, 100), api.verifyAuditChain()])
      .then(([evts, ch]) => { setEvents(evts); setChain(ch) })
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const download = async (format: 'json' | 'csv') => {
    const text = await api.exportAudit(format)
    const blob = new Blob([text], { type: format === 'csv' ? 'text/csv' : 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = `medtrust_audit.${format}`; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
            <BarChart3 size={20} color="#fbbf24" />
            <h1 className="page-title">Governance & Audit</h1>
          </div>
          <p className="page-subtitle">Cryptographic SHA-256 rolling hash chain · Tamper-evident audit ledger · HIPAA / SOC 2 compliance.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-ghost" onClick={() => download('csv')}><Download size={14} />CSV</button>
          <button className="btn btn-ghost" onClick={() => download('json')}><Download size={14} />JSON</button>
          <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} />Refresh</button>
        </div>
      </div>

      {/* Chain integrity card */}
      {chain && (
        <div className={`card ${chain.is_valid ? 'card-glow-emerald' : 'card-glow-rose'}`} style={{ padding: '1.25rem', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
            {chain.is_valid
              ? <CheckCircle2 size={32} color="#34d399" />
              : <XCircle size={32} color="#fb7185" />}
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: chain.is_valid ? '#34d399' : '#fb7185', marginBottom: '0.2rem' }}>
                {chain.is_valid ? '✓ Cryptographic Chain Intact & Verified' : '✕ Chain Integrity Alert — Tampering Detected'}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{chain.message}</div>
              <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.625rem' }}>
                <div><span style={{ fontSize: '0.7rem', color: '#475569' }}>Blocks Verified: </span><span style={{ fontWeight: 700, color: '#e2e8f0' }}>{chain.total_records}</span></div>
                <div><span style={{ fontSize: '0.7rem', color: '#475569' }}>Genesis: </span><code className="hash-chain">{chain.genesis_hash.slice(0, 24)}…</code></div>
                <div><span style={{ fontSize: '0.7rem', color: '#475569' }}>Head: </span><code className="hash-chain">{chain.latest_hash.slice(0, 24)}…</code></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audit ledger table */}
      <div className="card">
        <div style={{ padding: '0.875rem 1rem', borderBottom: '1px solid rgba(148,163,184,0.08)' }}>
          <div className="section-header" style={{ margin: 0 }}>Cryptographic Audit Ledger ({events.length} entries)</div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Event Type</th>
                <th>Actor</th>
                <th>Payload Hash</th>
                <th>Prev Hash</th>
                <th>Current Hash</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', padding: '2rem' }}><span className="spinner" /></td></tr>
              ) : events.map((e, i) => (
                <tr key={e.id}>
                  <td style={{ color: '#334155', fontFamily: 'monospace', fontSize: '0.72rem' }}>{i + 1}</td>
                  <td><code style={{ fontSize: '0.7rem', color: '#22d3ee' }}>{e.event_type}</code></td>
                  <td style={{ fontSize: '0.75rem', color: '#64748b' }}>{e.actor_id}</td>
                  <td><code className="hash-chain">{e.payload_hash.slice(0, 12)}…</code></td>
                  <td><code className="hash-chain">{e.prev_chain_hash.slice(0, 12)}…</code></td>
                  <td><code className="hash-chain">{e.current_chain_hash.slice(0, 12)}…</code></td>
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
