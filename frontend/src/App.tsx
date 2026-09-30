import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import AgentWorkspacePage from './pages/AgentWorkspacePage'
import DecisionReviewPage from './pages/DecisionReviewPage'
import ApprovalCenterPage from './pages/ApprovalCenterPage'
import AuditTrailPage from './pages/AuditTrailPage'
import ReplayPage from './pages/ReplayPage'
import InsightsPage from './pages/InsightsPage'
import PolicyPage from './pages/PolicyPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/agent" element={<AgentWorkspacePage />} />
      <Route path="/decisions" element={<DecisionReviewPage />} />
      <Route path="/approvals" element={<ApprovalCenterPage />} />
      <Route path="/audit" element={<AuditTrailPage />} />
      <Route path="/audit/replay" element={<ReplayPage />} />
      <Route path="/insights" element={<InsightsPage />} />
      <Route path="/policy" element={<PolicyPage />} />
    </Routes>
  )
}
