/**
 * MedTrust Engine API Client
 * Typed interface to the FastAPI backend.
 */

const BASE = '/api/v1'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ── Verification ─────────────────────────────────────────────

export interface VerifyRequest {
  query_text: string
}

export interface ClaimVerification {
  claim_text: string
  status: string
  grounding_score: number
  source_chunk_id: string
  document_version: string
  page_number: number
}

export interface VerifyResponse {
  query_id: string
  query_text: string
  final_status: string
  overall_confidence: number
  evidence_coverage_pct: number
  mean_grounding_score: number
  response_text: string
  claim_verifications: ClaimVerification[]
  human_review_required: boolean
  risk_tier: string
  pii_redacted: boolean
  pii_redaction_count: number
  security_cleared: boolean
  latency_ms: number
  has_contradiction: boolean
  contradiction_risk_score: number
  detected_conflicts: string[]
  created_at: string
}

export const api = {
  verify: (data: VerifyRequest) =>
    request<VerifyResponse>('/verify', { method: 'POST', body: JSON.stringify(data) }),

  // ── Documents ──────────────────────────────────────────────

  listDocuments: (skip = 0, limit = 50) =>
    request<DocumentRead[]>(`/documents?skip=${skip}&limit=${limit}`),

  uploadDocument: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return fetch(`${BASE}/documents/upload`, { method: 'POST', body: form }).then(r => r.json())
  },

  getDocument: (id: string) => request<DocumentRead>(`/documents/${id}`),

  // ── Security ───────────────────────────────────────────────

  scanQuery: (query_text: string) =>
    request<SecurityScanResponse>('/security/scan-query', { method: 'POST', body: JSON.stringify({ query_text }) }),

  listSecurityEvents: (skip = 0, limit = 50) =>
    request<SecurityEvent[]>(`/security/events?skip=${skip}&limit=${limit}`),

  getSecurityStats: () => request<SecurityStats>('/security/stats'),

  // ── Privacy ────────────────────────────────────────────────

  scanText: (text: string) =>
    request<PrivacyScanResponse>('/privacy/scan-text', { method: 'POST', body: JSON.stringify({ text }) }),

  listPrivacyEvents: (skip = 0, limit = 50) =>
    request<PrivacyEvent[]>(`/privacy/events?skip=${skip}&limit=${limit}`),

  getPrivacyStats: () => request<PrivacyStats>('/privacy/stats'),

  // ── Audit ──────────────────────────────────────────────────

  listAuditEvents: (skip = 0, limit = 100) =>
    request<AuditEvent[]>(`/audit/events?skip=${skip}&limit=${limit}`),

  verifyAuditChain: () => request<AuditChainVerification>('/audit/verify'),

  exportAudit: (format: 'json' | 'csv') =>
    fetch(`${BASE}/audit/export?format=${format}`).then(r => r.text()),

  // ── Governance ─────────────────────────────────────────────

  getGovernanceMetrics: () => request<GovernanceMetrics>('/governance/metrics'),

  // ── Evaluation ─────────────────────────────────────────────

  runBenchmark: (run_name = 'Lab Benchmark') =>
    request<EvaluationRun>('/evaluation/run', { method: 'POST', body: JSON.stringify({ run_name }) }),

  listEvaluationRuns: (skip = 0, limit = 20) =>
    request<EvaluationRun[]>(`/evaluation/runs?skip=${skip}&limit=${limit}`),

  getEvaluationRun: (id: string) => request<EvaluationRun>(`/evaluation/runs/${id}`),
}

// ── Type Definitions ──────────────────────────────────────────

export interface DocumentRead {
  id: string
  filename: string
  source_title: string
  document_version: string
  trust_tier: number
  is_active: boolean
  is_quarantined: boolean
  total_chunks: number
  file_sha256: string
  created_at: string
}

export interface SecurityScanResponse {
  is_safe: boolean
  threat_level: string
  threat_category: string | null
  action_taken: string
  detected_pattern: string | null
  sanitized_text: string
}

export interface SecurityEvent {
  id: string
  event_type: string
  threat_level: string
  source_type: string
  detected_pattern: string
  action_taken: string
  created_at: string
}

export interface SecurityStats {
  total_events: number
  blocked_count: number
  quarantined_count: number
  high_critical_count: number
  injection_catch_rate: number
}

export interface PrivacyScanResponse {
  has_pii: boolean
  total_redactions: number
  protected_text: string
  entities_detected: { entity_type: string; original: string; token: string }[]
  token_map: Record<string, string>
}

export interface PrivacyEvent {
  id: string
  source_type: string
  entity_type: string
  masked_snippet: string
  redacted_token: string
  created_at: string
}

export interface PrivacyStats {
  total_events: number
  pii_catch_rate: number
  entity_type_breakdown: Record<string, number>
}

export interface AuditEvent {
  id: string
  event_type: string
  actor_id: string
  query_id: string | null
  document_id: string | null
  payload_json: string
  payload_hash: string
  prev_chain_hash: string
  current_chain_hash: string
  created_at: string
}

export interface AuditChainVerification {
  is_valid: boolean
  total_records: number
  message: string
  genesis_hash: string
  latest_hash: string
}

export interface GovernanceMetrics {
  total_queries: number
  verified_count: number
  partial_count: number
  insufficient_count: number
  blocked_count: number
  contradictory_count: number
  review_required_count: number
  mean_evidence_coverage: number
  mean_grounding_accuracy: number
  mean_latency_ms: number
  total_documents: number
  quarantined_documents: number
  audit_chain_valid: boolean
  nist_controls: Record<string, { status: string; description: string; last_verified: string }>
}

export interface EvaluationCaseResult {
  id: string
  case_id: string
  case_category: string
  query_text: string
  expected_status: string
  actual_status: string
  passed: boolean
  latency_ms: number
  metrics_json: string
  created_at: string
}

export interface EvaluationRun {
  id: string
  run_name: string
  total_cases: number
  passed_cases: number
  failed_cases: number
  mean_evidence_coverage: number
  mean_grounding_accuracy: number
  injection_detection_rate: number
  pii_recall: number
  refusal_f1: number
  mean_latency_ms: number
  created_at: string
  case_results: EvaluationCaseResult[]
}
