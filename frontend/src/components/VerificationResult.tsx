import { type VerifyResponse, type ClaimVerification } from '../api'
import { CheckCircle2, XCircle, AlertTriangle, Clock, ShieldAlert, Minus } from 'lucide-react'

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { cls: string; label: string }> = {
    VERIFIED:             { cls: 'badge-verified',     label: '✓ Verified' },
    PARTIALLY_VERIFIED:   { cls: 'badge-partial',      label: '~ Partial' },
    INSUFFICIENT_EVIDENCE:{ cls: 'badge-insufficient', label: '○ Insufficient' },
    CONTRADICTORY:        { cls: 'badge-contradictory',label: '⚡ Contradictory' },
    BLOCKED:              { cls: 'badge-blocked',      label: '✕ Blocked' },
    REVIEW_REQUIRED:      { cls: 'badge-review',       label: '⬡ Review Required' },
    UNKNOWN:              { cls: 'badge-insufficient', label: '? Unknown' },
    SUPPORTED:            { cls: 'badge-verified',     label: '✓ Supported' },
    UNSUPPORTED:          { cls: 'badge-insufficient', label: '○ Unsupported' },
    CONTRADICTED:         { cls: 'badge-contradictory',label: '⚡ Contradicted' },
  }
  const cfg = map[status] ?? { cls: 'badge-insufficient', label: status }
  return <span className={`badge ${cfg.cls}`}>{cfg.label}</span>
}

export function TrustScore({ pct }: { pct: number }) {
  const color = pct >= 85 ? '#34d399' : pct >= 60 ? '#fbbf24' : '#fb7185'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <div className="progress-bar-wrap" style={{ flex: 1 }}>
        <div className="progress-bar-fill" style={{ width: `${pct}%`, background: `linear-gradient(90deg,${color}88,${color})` }} />
      </div>
      <span style={{ fontSize: '0.78rem', fontWeight: 600, color, minWidth: 36 }}>{pct.toFixed(0)}%</span>
    </div>
  )
}

export function ClaimCard({ claim }: { claim: ClaimVerification }) {
  const icon = {
    SUPPORTED: <CheckCircle2 size={14} color="#34d399" />,
    UNSUPPORTED: <Minus size={14} color="#94a3b8" />,
    CONTRADICTED: <XCircle size={14} color="#fb923c" />,
    BLOCKED: <ShieldAlert size={14} color="#fb7185" />,
  }[claim.status] ?? <AlertTriangle size={14} color="#fbbf24" />

  return (
    <div className="evidence-block" style={{ marginBottom: '0.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
        <p style={{ margin: 0, color: '#cbd5e1', lineHeight: 1.6 }}>{claim.claim_text}</p>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem', minWidth: 120 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>{icon}<StatusBadge status={claim.status} /></div>
          <span className="chunk-id">G:{(claim.grounding_score * 100).toFixed(0)}%</span>
          <span className="chunk-id" style={{ color: '#475569' }}>v{claim.document_version} p.{claim.page_number}</span>
        </div>
      </div>
    </div>
  )
}

export function VerificationResult({ result }: { result: VerifyResponse }) {
  return (
    <div className="card fade-in" style={{ padding: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
            <StatusBadge status={result.final_status} />
            {result.risk_tier && <span className="badge" style={{ background: 'rgba(167,139,250,0.12)', color: '#c4b5fd', border: '1px solid rgba(167,139,250,0.3)' }}>{result.risk_tier}</span>}
            {result.human_review_required && <span className="badge badge-review">Human Review</span>}
            {result.pii_redacted && <span className="badge" style={{ background: 'rgba(6,182,212,0.12)', color: '#22d3ee', border: '1px solid rgba(6,182,212,0.3)' }}>PII ({result.pii_redaction_count})</span>}
            {result.has_contradiction && <span className="badge badge-contradictory">Contradiction ({(result.contradiction_risk_score * 100).toFixed(0)}%)</span>}
            {!result.security_cleared && <span className="badge badge-blocked">Threat Blocked</span>}
          </div>
          <p style={{ margin: 0, fontSize: '0.78rem', color: '#64748b' }}>
            Query ID: <code style={{ color: '#34d399', fontSize: '0.72rem' }}>{result.query_id}</code>
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: '#64748b', fontSize: '0.75rem' }}>
          <Clock size={13} />
          {result.latency_ms.toFixed(1)}ms
        </div>
      </div>

      {/* Trust metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.875rem', marginBottom: '1rem' }}>
        <MetricTile label="Evidence Coverage" value={`${result.evidence_coverage_pct.toFixed(0)}%`} />
        <MetricTile label="Mean Grounding" value={`${(result.mean_grounding_score * 100).toFixed(0)}%`} />
        <MetricTile label="Confidence" value={`${(result.overall_confidence * 100).toFixed(0)}%`} />
      </div>
      <TrustScore pct={result.evidence_coverage_pct} />

      {/* Conflicts */}
      {result.detected_conflicts.length > 0 && (
        <div style={{ marginTop: '0.875rem', background: 'rgba(249,115,22,0.08)', border: '1px solid rgba(249,115,22,0.2)', borderRadius: '0.5rem', padding: '0.75rem 1rem' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#fb923c', textTransform: 'uppercase', marginBottom: '0.3rem' }}>⚡ Guideline Conflicts Detected</div>
          {result.detected_conflicts.map((c, i) => <p key={i} style={{ margin: 0, fontSize: '0.8rem', color: '#fdba74' }}>{c}</p>)}
        </div>
      )}

      {/* Synthesized response */}
      <div style={{ marginTop: '1rem' }}>
        <div className="section-header">Synthesized Clinical Response</div>
        <div style={{ background: 'rgba(2,6,23,0.6)', border: '1px solid rgba(148,163,184,0.1)', borderRadius: '0.5rem', padding: '0.875rem 1rem', fontSize: '0.85rem', lineHeight: 1.75, color: '#cbd5e1', whiteSpace: 'pre-wrap' }}>
          {result.response_text}
        </div>
      </div>

      {/* Claim verifications */}
      {result.claim_verifications.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <div className="section-header">Atomic Claim Verifications ({result.claim_verifications.length})</div>
          {result.claim_verifications.map((c, i) => <ClaimCard key={i} claim={c} />)}
        </div>
      )}
    </div>
  )
}

function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: 'rgba(15,23,42,0.5)', borderRadius: '0.5rem', padding: '0.625rem 0.875rem', textAlign: 'center' }}>
      <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#e2e8f0' }}>{value}</div>
      <div style={{ fontSize: '0.68rem', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.1rem' }}>{label}</div>
    </div>
  )
}
