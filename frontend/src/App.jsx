import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Sidebar from './components/Sidebar'
import PageTransition from './components/PageTransition'
import ProtectedRoute from './auth/ProtectedRoute'
import Login from './pages/Login'
import Overview from './pages/Overview'
import Gateway from './pages/Gateway'
import Dashboard from './pages/Dashboard'
import Approvals from './pages/Approvals'
import PolicyRules from './pages/PolicyRules'
import Reports from './pages/Reports'
import Integrations from './pages/Integrations'
import { useAuth } from './auth/AuthContext'

function AppShell() {
  const location = useLocation()
  const { user } = useAuth()

  if (!user) {
    return (
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="*" element={<PageTransition><Login /></PageTransition>} />
        </Routes>
      </AnimatePresence>
    )
  }

  return (
    <div className="flex min-h-screen bg-bg text-ink font-body">
      <Sidebar />
      <main className="flex-1 min-w-0 pb-16 md:pb-0">
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/login" element={<PageTransition><Login /></PageTransition>} />
            <Route path="/" element={<PageTransition><ProtectedRoute><Overview /></ProtectedRoute></PageTransition>} />
            <Route path="/gateway" element={<PageTransition><ProtectedRoute><Gateway /></ProtectedRoute></PageTransition>} />
            <Route path="/dashboard" element={<PageTransition><ProtectedRoute><Dashboard /></ProtectedRoute></PageTransition>} />
            <Route path="/approvals" element={<PageTransition><ProtectedRoute adminOnly><Approvals /></ProtectedRoute></PageTransition>} />
            <Route path="/policy" element={<PageTransition><ProtectedRoute adminOnly><PolicyRules /></ProtectedRoute></PageTransition>} />
            <Route path="/reports" element={<PageTransition><ProtectedRoute adminOnly><Reports /></ProtectedRoute></PageTransition>} />
            <Route path="/integrations" element={<PageTransition><ProtectedRoute><Integrations /></ProtectedRoute></PageTransition>} />
          </Routes>
        </AnimatePresence>
      </main>
    </div>
  )
}

export default function App() {
  return <AppShell />
}
