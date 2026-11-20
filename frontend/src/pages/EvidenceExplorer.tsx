import { useState } from 'react'
import { api, type VerifyResponse } from '../api'
import { VerificationResult } from '../components/VerificationResult'
import { BookOpen, Search } from 'lucide-react'

export default function EvidenceExplorer() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<VerifyResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = async () => {
    if (!query.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      setResult(await api.verify({ query_text: query }))
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
        <BookOpen size={20} color="#a78bfa" />
        <h1 className="page-title">Evidence Explorer</h1>
      </div>
      <p className="page-subtitle" style={{ marginBottom: '1.75rem' }}>Drill into exact evidence chunks, provenance chains, and claim-level grounding scores.</p>

      <div className="card" style={{ padding: '1.25rem', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            className="input"
            placeholder="Query clinical evidence (e.g. 'Norepinephrine MAP target for septic shock')…"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()}
          />
          <button className="btn btn-primary" onClick={search} disabled={loading || !query.trim()}>
            {loading ? <span className="spinner" /> : <Search size={14} />}
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>
      </div>

      {error && <div style={{ color: '#fb7185', fontSize: '0.85rem', marginBottom: '1rem' }}>✕ {error}</div>}

      {result && (
        <div>
          <VerificationResult result={result} />

          {result.claim_verifications.length > 0 && (
            <div className="card" style={{ padding: '1.25rem', marginTop: '1rem' }}>
              <div className="section-header">Raw Evidence Provenance Trace</div>
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Claim Extract</th>
                      <th>Status</th>
                      <th>Grounding</th>
                      <th>Chunk ID</th>
                      <th>Version</th>
                      <th>Page</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.claim_verifications.map((c, i) => (
                      <tr key={i}>
                        <td style={{ color: '#475569' }}>{i + 1}</td>
                        <td style={{ maxWidth: 280 }}>{c.claim_text.slice(0, 80)}{c.claim_text.length > 80 && '…'}</td>
                        <td><span className={`badge badge-${c.status.toLowerCase().replace('_', '-')}`}>{c.status}</span></td>
                        <td style={{ color: '#34d399', fontWeight: 600 }}>{(c.grounding_score * 100).toFixed(0)}%</td>
                        <td><code style={{ fontSize: '0.7rem', color: '#a78bfa' }}>{c.source_chunk_id.slice(0, 12)}…</code></td>
                        <td><code style={{ fontSize: '0.72rem', color: '#fbbf24' }}>v{c.document_version}</code></td>
                        <td>{c.page_number}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
