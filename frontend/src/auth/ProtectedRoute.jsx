import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { user, ready, isAdmin } = useAuth()
  const location = useLocation()

  if (!ready) return null // wait for localStorage check to finish before deciding

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (adminOnly && !isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-24 text-center px-6">
        <p className="font-display text-lg font-semibold text-ink mb-1">Admins only</p>
        <p className="text-sm text-muted max-w-xs">Your account doesn't have access to this page. Ask an admin if you need it.</p>
      </div>
    )
  }

  return children
}
