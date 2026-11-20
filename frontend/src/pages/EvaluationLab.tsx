import { useEffect, useState } from 'react'
import { api, type EvaluationRun } from '../api'
import { FlaskConical, Play, RefreshCw, CheckCircle2, XCircle, Trophy } from 'lucide-react'
import { TrustScore } from '../components/VerificationResult'

export default function EvaluationLab() {
  const [runs, setRuns] = useState<EvaluationRun[]>([])
  const [selected, setSelected] = useState<EvaluationRun | null>(null)
  const [running, setRunning] = useState(false)
  const [loading, setLoading] = useState(true)
  const [runName, setRunName] = useState('Lab Benchmark')

  const load = () => {
    setLoading(true)
    api.listEvaluationRuns(0, 20)
      .then(r => { setRuns(r); if (r.length > 0 && !selected) setSelected(r[0]) })
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const runBenchmark = async () => {
    setRunning(true)
    try {
      const run = await api.runBenchmark(runName)
      const full = await api.getEvaluationRun(run.id)
      setSelected(full)
      setRuns(prev => [full, ...prev])
    } catch (e: any) {
      alert('Benchmark failed: ' + e.message)
    } finally {
      setRunning(false)
    }
  }

  const passRate = (run: EvaluationRun) => ((run.passed_cases / run.total_cases) * 100).toFixed(0)

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
            <FlaskConical size={20} color="#34d399" />
            <h1 className="page-title">Evaluation Lab</h1>
          </div>
          <p className="page-subtitle">10-point adversarial benchmark suite — evidence grounding, injection defense, privacy, refusal integrity.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input className="input" style={{ width: 180 }} value={runName} onChange={e => setRunName(e.target.value)} placeholder="Run name" />
          <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /></button>
          <button className="btn btn-primary" onClick={runBenchmark} disabled={running}>
            {running ? <span className="spinner" /> : <Play size={14} />}
            {running ? 'Running…' : 'Run Benchmark'}
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '1.25rem' }}>
        {/* Runs list */}
        <div>
          <div className="section-header">Benchmark History</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {loading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}><span className="spinner" /></div>
            ) : runs.length === 0 ? (
              <div className="card" style={{ padding: '1rem', textAlign: 'center', color: '#475569', fontSize: '0.82rem' }}>No runs yet. Click "Run Benchmark".</div>
            ) : runs.map(r => (
              <div key={r.id} className="card" onClick={() => api.getEvaluationRun(r.id).then(setSelected)}
                style={{ padding: '0.875rem', cursor: 'pointer', border: selected?.id === r.id ? '1px solid rgba(16,185,129,0.4)' : undefined, borderRadius: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1' }}>{r.run_name}</span>
                  <span style={{ fontWeight: 700, color: parseInt(passRate(r)) >= 80 ? '#34d399' : '#fb7185', fontSize: '0.85rem' }}>{passRate(r)}%</span>
                </div>
                <div style={{ fontSize: '0.7rem', color: '#475569' }}>{r.passed_cases}/{r.total_cases} cases · {new Date(r.created_at).toLocaleDateString()}</div>
                <div style={{ marginTop: '0.375rem' }}><TrustScore pct={parseFloat(passRate(r))} /></div>
              </div>
            ))}
          </div>
        </div>

        {/* Run detail */}
        {selected ? (
          <div>
            {/* Metrics summary */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.875rem', marginBottom: '1.25rem' }}>
              <MetricCard label="Pass Rate" value={`${passRate(selected)}%`} color={parseInt(passRate(selected)) >= 80 ? '#34d399' : '#fb7185'} icon={<Trophy size={16} />} />
              <MetricCard label="Injection Catch" value={`${selected.injection_detection_rate.toFixed(0)}%`} color="#fb7185" />
              <MetricCard label="PII Recall" value={`${selected.pii_recall.toFixed(0)}%`} color="#22d3ee" />
              <MetricCard label="Refusal F1" value={`${selected.refusal_f1.toFixed(0)}%`} color="#a78bfa" />
              <MetricCard label="Evidence Coverage" value={`${selected.mean_evidence_coverage.toFixed(1)}%`} color="#fbbf24" />
              <MetricCard label="Avg Latency" value={`${selected.mean_latency_ms.toFixed(0)}ms`} color="#34d399" />
            </div>

            {/* Case results */}
            <div className="card">
              <div style={{ padding: '0.875rem 1rem', borderBottom: '1px solid rgba(148,163,184,0.08)' }}>
                <div className="section-header" style={{ margin: 0 }}>10-Case Scenario Results</div>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Case</th>
                      <th>Category</th>
                      <th>Expected</th>
                      <th>Actual</th>
                      <th>Result</th>
                      <th>Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.case_results.map(c => (
                      <tr key={c.id}>
                        <td><code style={{ fontSize: '0.75rem', color: '#a78bfa' }}>{c.case_id}</code></td>
                        <td style={{ fontSize: '0.75rem', color: '#64748b', maxWidth: 160 }}>{c.case_category}</td>
                        <td><span className="badge badge-insufficient" style={{ fontSize: '0.65rem' }}>{c.expected_status}</span></td>
                        <td>
                          <span className={`badge ${statusBadgeCls(c.actual_status)}`} style={{ fontSize: '0.65rem' }}>{c.actual_status}</span>
                        </td>
                        <td>
                          {c.passed
                            ? <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#34d399', fontSize: '0.75rem', fontWeight: 600 }}><CheckCircle2 size={13} />PASS</span>
                            : <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#fb7185', fontSize: '0.75rem', fontWeight: 600 }}><XCircle size={13} />FAIL</span>}
                        </td>
                        <td style={{ fontSize: '0.75rem', color: '#475569' }}>{c.latency_ms.toFixed(0)}ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 300, color: '#475569', fontSize: '0.85rem' }}>
            Select a benchmark run to view results
          </div>
        )}
      </div>
    </div>
  )
}

function MetricCard({ label, value, color, icon }: { label: string; value: string; color: string; icon?: React.ReactNode }) {
  return (
    <div className="card" style={{ padding: '1rem 1.25rem' }}>
      <div style={{ fontSize: '0.68rem', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>{icon}{label}</div>
      <div style={{ fontSize: '1.4rem', fontWeight: 700, color }}>{value}</div>
    </div>
  )
}

function statusBadgeCls(s: string) {
  const map: Record<string, string> = { VERIFIED: 'badge-verified', PARTIALLY_VERIFIED: 'badge-partial', INSUFFICIENT_EVIDENCE: 'badge-insufficient', CONTRADICTORY: 'badge-contradictory', BLOCKED: 'badge-blocked', REVIEW_REQUIRED: 'badge-review' }
  return map[s] ?? 'badge-insufficient'
}
