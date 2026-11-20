import { type ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import {
  Activity, FileText, Search, Shield, Lock,
  BookOpen, FlaskConical, Settings, BarChart3, ClipboardList
} from 'lucide-react'

const NAV = [
  { to: '/',           icon: Activity,      label: 'Dashboard' },
  { to: '/workspace',  icon: Search,        label: 'Clinical Workspace' },
  { to: '/documents',  icon: FileText,      label: 'Document Library' },
  { to: '/evidence',   icon: BookOpen,      label: 'Evidence Explorer' },
  { to: '/review',     icon: ClipboardList, label: 'Review Queue' },
  { to: '/security',   icon: Shield,        label: 'Security Center' },
  { to: '/privacy',    icon: Lock,          label: 'Privacy Center' },
  { to: '/governance', icon: BarChart3,     label: 'Governance & Audit' },
  { to: '/evaluation', icon: FlaskConical,  label: 'Evaluation Lab' },
  { to: '/settings',   icon: Settings,      label: 'Settings' },
]

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        <div className="page fade-in">{children}</div>
      </main>
    </div>
  )
}

function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div style={{ padding: '1.25rem 1rem 1rem', borderBottom: '1px solid rgba(148,163,184,0.1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{
            width: 32, height: 32, borderRadius: '0.5rem',
            background: 'linear-gradient(135deg,#059669,#0e7490)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 16px rgba(16,185,129,0.4)',
          }}>
            <Activity size={16} color="#fff" />
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', letterSpacing: '-0.01em' }}>MedTrust</div>
            <div style={{ fontSize: '0.65rem', color: '#475569', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Engine v1.0</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '0.75rem 0' }}>
        <div className="section-header" style={{ padding: '0 1rem', marginBottom: '0.5rem' }}>Navigation</div>
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <Icon size={15} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{ padding: '0.875rem 1rem', borderTop: '1px solid rgba(148,163,184,0.1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="pulse-dot green" />
          <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Engine Online</span>
        </div>
        <div style={{ fontSize: '0.65rem', color: '#334155', marginTop: '0.25rem' }}>NIST AI RMF 1.0 Aligned</div>
      </div>
    </aside>
  )
}
