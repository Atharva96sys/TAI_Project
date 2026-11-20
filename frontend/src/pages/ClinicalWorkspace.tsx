import { useState } from 'react'
import { api, type VerifyResponse } from '../api'
import { VerificationResult } from '../components/VerificationResult'
import { Send, Microscope, Zap } from 'lucide-react'

const QUICK_QUERIES = [
  'When should broad-spectrum antimicrobials be administered in sepsis?',
  'What is the first-line vasopressor for septic shock?',
  'What is the fluid resuscitation protocol for septic shock?',
  'What is the correct dose of Enoxaparin 40 mg subcutaneous for DVT prophylaxis?',
  'What is the gene therapy CRISPR dosage for Huntington\'s disease?',
]

export default function ClinicalWorkspace() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<VerifyResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (q?: string) => {
    const text = q ?? query
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await api.verify({ query_text: text })
      setResult(res)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
          <Microscope size={20} color="#34d399" />
          <h1 className="page-title">Clinical Workspace</h1>
        </div>
        <p className="page-subtitle">Submit clinical queries for evidence-grounded verification against indexed guidelines.</p>
      </div>

      {/* Query Input */}
      <div className="card gradient-border" style={{ padding: '1.5rem', marginBottom: '1.25rem' }}>
        <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: '0.5rem' }}>
          Clinical Query
        </label>
        <textarea
          className="input"
          rows={4}
          placeholder="Enter clinical query — e.g. 'What is the first-line vasopressor for septic shock according to 2026 guidelines?'"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) submit() }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.75rem' }}>
          <span style={{ fontSize: '0.72rem', color: '#334155' }}>Ctrl+Enter to submit · Security Airlock + Privacy Shield active</span>
          <button className="btn btn-primary" onClick={() => submit()} disabled={loading || !query.trim()}>
            {loading ? <span className="spinner" /> : <Send size={14} />}
            {loading ? 'Verifying…' : 'Verify Query'}
          </button>
        </div>
      </div>

      {/* Quick queries */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div className="section-header" style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <Zap size={11} /> Quick Clinical Scenarios
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {QUICK_QUERIES.map((q, i) => (
            <button
              key={i}
              className="btn btn-ghost"
              style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
              onClick={() => { setQuery(q); submit(q) }}
              disabled={loading}
            >
              {q.length > 55 ? q.slice(0, 55) + '…' : q}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{ background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.25)', borderRadius: '0.5rem', padding: '0.875rem 1rem', color: '#fb7185', fontSize: '0.85rem', marginBottom: '1rem' }}>
          ✕ {error}
        </div>
      )}

      {/* Result */}
      {result && <VerificationResult result={result} />}
    </div>
  )
}
