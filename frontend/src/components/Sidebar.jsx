import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ShieldCheck, ScanLine as ScanIcon, LayoutDashboard, ListChecks, FileBarChart, Puzzle, ClipboardCheck, LogOut } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: ShieldCheck, end: true, adminOnly: false },
  { to: '/gateway', label: 'Gateway', icon: ScanIcon, adminOnly: false },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, adminOnly: false },
  { to: '/approvals', label: 'Approvals', icon: ClipboardCheck, adminOnly: true },
  { to: '/policy', label: 'Policy Rules', icon: ListChecks, adminOnly: true },
  { to: '/reports', label: 'Reports', icon: FileBarChart, adminOnly: true },
  { to: '/integrations', label: 'Integrations', icon: Puzzle, adminOnly: false },
]

export default function Sidebar() {
  const { user, isAdmin, logout } = useAuth()
  const items = NAV_ITEMS.filter(item => !item.adminOnly || isAdmin)

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:flex-col w-60 shrink-0 border-r border-line bg-surface/60 h-screen sticky top-0">
        <div className="flex items-center gap-2 px-5 h-16 border-b border-line">
          <ShieldCheck size={22} className="text-brand" />
          <span className="font-display font-semibold text-ink tracking-tight">Sentinel</span>
        </div>
        <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
          {items.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand/10 text-brand'
                    : 'text-muted hover:text-ink hover:bg-surface-2'
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>
        {user && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="px-4 py-3 border-t border-line flex items-center gap-2.5"
          >
            <div className="w-8 h-8 rounded-full bg-brand/15 text-brand flex items-center justify-center text-xs font-display font-semibold shrink-0">
              {(user.full_name || user.username).slice(0, 1).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-ink truncate">{user.full_name || user.username}</p>
              <p className="text-[10px] text-muted capitalize">{user.role} &middot; {user.department}</p>
            </div>
            <button onClick={logout} title="Log out" className="text-muted hover:text-danger transition shrink-0">
              <LogOut size={15} />
            </button>
          </motion.div>
        )}
        <div className="px-5 py-3 border-t border-line text-xs text-muted">
          Sentinel AI v2.1 &middot; local instance
        </div>
      </aside>

      {/* Mobile bottom nav - horizontally scrollable so all items fit
          without truncating on narrow phone screens */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-surface border-t border-line overflow-x-auto">
        <div className="flex py-2 min-w-max px-1">
          {items.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 px-3 py-1 text-[10px] font-medium whitespace-nowrap shrink-0 ${
                  isActive ? 'text-brand' : 'text-muted'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </div>
      </nav>
    </>
  )
}
