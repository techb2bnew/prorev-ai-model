import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import ApiLogPanel from './components/ApiLogPanel.jsx'
import { Spinner } from './components/common.jsx'
import { useAuth } from './context/AuthContext.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import HealthPage from './pages/HealthPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import InspectionDetailPage from './pages/InspectionDetailPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import NewInspectionPage from './pages/NewInspectionPage.jsx'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '◫', end: true },
  { to: '/inspect', label: 'New Inspection', icon: '＋' },
  { to: '/history', label: 'History', icon: '⏱' },  
  { to: '/system', label: 'System & API', icon: '⚙' },
]

export default function App() {
  const { user, loading, signOut } = useAuth()

  if (loading) {
    return (
      <div className="auth-shell">
        <div className="row"><Spinner /> <span className="muted">Restoring session…</span></div>
      </div>
    )
  }

  if (!user) return <LoginPage />

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">D</div>
          <div>
            <div className="brand-name">Dent Detection</div>
            <div className="brand-sub">YOLO11m · v1.0</div>
          </div>
        </div>

        <nav className="nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              <span style={{ width: 14, textAlign: 'center' }}>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-foot">
          <div className="sidebar-user">
            <span className="small muted">Signed in</span>
            <strong>{user.email}</strong>
            <span className="small muted">{user.role}</span>
          </div>
          <button className="btn-sm btn-ghost" style={{ width: '100%' }} onClick={signOut}>
            Sign out
          </button>
        </div>
      </aside>

      <div className="main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/inspect" element={<NewInspectionPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/inspections/:id" element={<InspectionDetailPage />} />
          <Route path="/system" element={<HealthPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <ApiLogPanel />
      </div>
    </div>
  )
}
