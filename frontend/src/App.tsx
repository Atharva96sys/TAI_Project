import './index.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import Dashboard         from './pages/Dashboard'
import ClinicalWorkspace from './pages/ClinicalWorkspace'
import DocumentLibrary   from './pages/DocumentLibrary'
import EvidenceExplorer  from './pages/EvidenceExplorer'
import ReviewQueue       from './pages/ReviewQueue'
import SecurityCenter    from './pages/SecurityCenter'
import PrivacyCenter     from './pages/PrivacyCenter'
import GovernanceAudit   from './pages/GovernanceAudit'
import EvaluationLab     from './pages/EvaluationLab'
import Settings          from './pages/Settings'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/"           element={<Dashboard />} />
          <Route path="/workspace"  element={<ClinicalWorkspace />} />
          <Route path="/documents"  element={<DocumentLibrary />} />
          <Route path="/evidence"   element={<EvidenceExplorer />} />
          <Route path="/review"     element={<ReviewQueue />} />
          <Route path="/security"   element={<SecurityCenter />} />
          <Route path="/privacy"    element={<PrivacyCenter />} />
          <Route path="/governance" element={<GovernanceAudit />} />
          <Route path="/evaluation" element={<EvaluationLab />} />
          <Route path="/settings"   element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
