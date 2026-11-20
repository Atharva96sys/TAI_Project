import { useEffect, useState, useRef } from 'react'
import { api, type DocumentRead } from '../api'
import { FileText, Upload, CheckCircle2, AlertTriangle, ShieldAlert, RefreshCw } from 'lucide-react'

export default function DocumentLibrary() {
  const [docs, setDocs] = useState<DocumentRead[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const load = () => {
    setLoading(true)
    api.listDocuments(0, 100)
      .then(setDocs)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setUploadMsg(null)
    try {
      const res = await api.uploadDocument(file)
      setUploadMsg(`✓ "${file.name}" ingested — ${res.total_chunks ?? '?'} chunks indexed`)
      load()
    } catch (err: any) {
      setUploadMsg(`✕ Upload failed: ${err.message}`)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const tierColor = (t: number) => ['#34d399','#22d3ee','#fbbf24','#fb923c','#fb7185'][t - 1] ?? '#64748b'
  const tierLabel = (t: number) => ['Tier 1 – Authority','Tier 2 – Protocol','Tier 3 – Clinical SOP','Tier 4 – Research','Tier 5 – Unverified'][t - 1] ?? `Tier ${t}`

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
            <FileText size={20} color="#22d3ee" />
            <h1 className="page-title">Document Library</h1>
          </div>
          <p className="page-subtitle">Clinical guidelines indexed in FAISS / BM25 retrieval engine.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} />Refresh</button>
          <label className="btn btn-primary" style={{ cursor: 'pointer' }}>
            {uploading ? <span className="spinner" /> : <Upload size={14} />}
            {uploading ? 'Uploading…' : 'Upload PDF'}
            <input ref={fileRef} type="file" accept=".pdf,.txt" style={{ display: 'none' }} onChange={handleUpload} disabled={uploading} />
          </label>
        </div>
      </div>

      {uploadMsg && (
        <div style={{ background: uploadMsg.startsWith('✓') ? 'rgba(16,185,129,0.08)' : 'rgba(244,63,94,0.08)', border: `1px solid ${uploadMsg.startsWith('✓') ? 'rgba(16,185,129,0.25)' : 'rgba(244,63,94,0.25)'}`, borderRadius: '0.5rem', padding: '0.75rem 1rem', fontSize: '0.85rem', color: uploadMsg.startsWith('✓') ? '#34d399' : '#fb7185', marginBottom: '1rem' }}>
          {uploadMsg}
        </div>
      )}

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Document</th>
                <th>Version</th>
                <th>Trust Tier</th>
                <th>Chunks</th>
                <th>SHA-256</th>
                <th>Status</th>
                <th>Ingested</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: '#475569' }}><span className="spinner" /></td></tr>
              ) : docs.length === 0 ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: '#475569' }}>No documents indexed. Upload a PDF to begin.</td></tr>
              ) : docs.map(d => (
                <tr key={d.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <FileText size={13} color="#22d3ee" />
                      <div>
                        <div style={{ color: '#e2e8f0', fontWeight: 500 }}>{d.source_title}</div>
                        <div style={{ fontSize: '0.7rem', color: '#475569' }}>{d.filename}</div>
                      </div>
                    </div>
                  </td>
                  <td><code style={{ fontSize: '0.75rem', color: '#fbbf24' }}>{d.document_version}</code></td>
                  <td><span style={{ fontSize: '0.72rem', fontWeight: 600, color: tierColor(d.trust_tier) }}>{tierLabel(d.trust_tier)}</span></td>
                  <td style={{ textAlign: 'center', color: '#34d399', fontWeight: 600 }}>{d.total_chunks}</td>
                  <td><code className="hash-chain" style={{ fontSize: '0.65rem' }}>{d.file_sha256.slice(0, 16)}…</code></td>
                  <td>
                    {d.is_quarantined ? (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.72rem', color: '#fb7185' }}><ShieldAlert size={12} />Quarantined</span>
                    ) : d.is_active ? (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.72rem', color: '#34d399' }}><CheckCircle2 size={12} />Active</span>
                    ) : (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.72rem', color: '#64748b' }}><AlertTriangle size={12} />Inactive</span>
                    )}
                  </td>
                  <td style={{ color: '#475569', fontSize: '0.75rem' }}>{new Date(d.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
