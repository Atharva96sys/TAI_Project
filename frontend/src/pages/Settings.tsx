import { Settings, Info, CheckCircle2 } from 'lucide-react'

const SETTINGS_GROUPS = [
  {
    title: 'Backend Configuration',
    items: [
      { label: 'API Base URL', value: '/api/v1', note: 'Proxied to http://127.0.0.1:8000' },
      { label: 'LLM Provider', value: 'DeterministicClinicalEngine', note: 'No API key required — fully offline grounding' },
      { label: 'Embedding Model', value: 'all-MiniLM-L6-v2 (384-dim)', note: 'Sentence-transformers, CPU-optimized' },
      { label: 'Vector Index', value: 'FAISS (IndexFlatIP)', note: 'Inner-product cosine similarity' },
      { label: 'Sparse Index', value: 'BM25 (Okapi)', note: 'Lexical keyword retrieval' },
      { label: 'Fusion Strategy', value: 'Hybrid RRF (α=0.7)', note: 'Reciprocal Rank Fusion' },
    ],
  },
  {
    title: 'Security Policy',
    items: [
      { label: 'Direct Injection Patterns', value: '15 patterns', note: 'Jailbreak, persona, system exfiltration' },
      { label: 'Indirect Injection Patterns', value: '8 patterns', note: 'Document poisoning, delimiter injection' },
      { label: 'XML Evidence Delimiter', value: '<untrusted_clinical_evidence>', note: 'Isolates retrieved text from system prompt' },
      { label: 'Airlock Default Action', value: 'BLOCK on threat', note: 'Zero LLM dispatch for HIGH/CRITICAL threats' },
    ],
  },
  {
    title: 'Privacy & HIPAA',
    items: [
      { label: 'HIPAA Identifiers Covered', value: '18 Safe Harbor entities', note: 'Name, MRN, DOB, SSN, phone, email, address, ZIP…' },
      { label: 'Pseudonymization Format', value: '[ENTITY_001] tokens', note: 'Deterministic, reversible within session' },
      { label: 'Tier 5 Safety Block', value: 'Enabled', note: 'Patient-specific clinical queries hard-blocked' },
    ],
  },
  {
    title: 'Audit Ledger',
    items: [
      { label: 'Hash Algorithm', value: 'SHA-256', note: 'FIPS 180-4 compliant' },
      { label: 'Genesis Hash', value: '0'.repeat(64), note: 'Deterministic chain anchor' },
      { label: 'Chain Formula', value: 'SHA256(prev_hash:payload_hash:iso_timestamp)', note: 'Rolling tamper-evident linkage' },
      { label: 'Export Formats', value: 'JSON, CSV', note: 'Available from Governance & Audit page' },
    ],
  },
  {
    title: 'Risk Engine Tiers',
    items: [
      { label: 'Tier 1 — General', value: 'Pass-through', note: 'No risk escalation' },
      { label: 'Tier 2 — Interpretive', value: 'Low risk', note: 'Educational/diagnostic concepts' },
      { label: 'Tier 3 — Clinical Recommendation', value: 'Medium risk', note: 'Treatment selection queries' },
      { label: 'Tier 4 — Dosage & Treatment', value: 'REVIEW_REQUIRED', note: 'Numeric thresholds, drug dosing' },
      { label: 'Tier 5 — Patient-Specific', value: 'BLOCKED', note: 'PHI-containing queries hard-blocked' },
    ],
  },
]

export default function SettingsPage() {
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
        <Settings size={20} color="#94a3b8" />
        <h1 className="page-title">Settings & Configuration</h1>
      </div>
      <p className="page-subtitle" style={{ marginBottom: '1.75rem' }}>System configuration, policy settings, and compliance information.</p>

      {/* Info banner */}
      <div style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '0.625rem', padding: '0.875rem 1.125rem', marginBottom: '1.5rem', display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
        <Info size={16} color="#34d399" style={{ flexShrink: 0, marginTop: 2 }} />
        <div>
          <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#34d399', marginBottom: '0.2rem' }}>Offline-First Architecture</div>
          <div style={{ fontSize: '0.78rem', color: '#64748b', lineHeight: 1.6 }}>
            MedTrust Engine operates fully offline with zero external API calls. The DeterministicClinicalEngine synthesizes responses exclusively from indexed, cryptographically-hashed clinical guidelines. No patient data, query text, or clinical responses are transmitted to external servers.
          </div>
        </div>
      </div>

      {SETTINGS_GROUPS.map(group => (
        <div key={group.title} className="card" style={{ padding: '1.25rem', marginBottom: '1rem' }}>
          <div className="section-header">{group.title}</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.625rem' }}>
            {group.items.map(item => (
              <div key={item.label} style={{ padding: '0.75rem', background: 'rgba(15,23,42,0.5)', borderRadius: '0.5rem', border: '1px solid rgba(148,163,184,0.07)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>{item.label}</span>
                  <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#e2e8f0', textAlign: 'right' }}>{item.value}</span>
                </div>
                <div style={{ fontSize: '0.7rem', color: '#334155', marginTop: '0.15rem' }}>{item.note}</div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Framework compliance */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <div className="section-header">Regulatory & Framework Compliance</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.625rem' }}>
          {[
            'NIST AI RMF 1.0 (GOVERN · MAP · MEASURE · MANAGE)',
            'EU AI Act (High-Risk Medical Device Provisions)',
            'HIPAA 45 CFR §164.514(b) Safe Harbor',
            'FDA 21 CFR Part 11 (Audit Trail)',
            'SOC 2 Type II (Audit Logging)',
            'ISO 27001 (Information Security)',
          ].map(f => (
            <div key={f} style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)', borderRadius: '0.5rem', padding: '0.4rem 0.75rem', fontSize: '0.75rem', color: '#34d399' }}>
              <CheckCircle2 size={12} />{f}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
