import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { ROLE_LABELS, useAuth } from '../auth/AuthContext'

// role -> which nav items are visible
const NAV = [
  { to: '/', label: 'Dashboard', icon: '📊', roles: 'all' },
  { to: '/employees', label: 'Employees', icon: '👥', roles: 'all' },
  { to: '/attendance', label: 'Attendance', icon: '🗓️', roles: 'all' },
  { to: '/payroll', label: 'Payroll', icon: '💰', roles: 'all' },
  { to: '/performance', label: 'Performance', icon: '🎯', roles: 'all' },
  { to: '/recruitment', label: 'Recruitment', icon: '📄', roles: ['management_admin', 'senior_manager', 'hr_recruiter'] },
  { to: '/voice-agent', label: 'Voice Screening', icon: '🎙️', roles: ['management_admin', 'senior_manager', 'hr_recruiter'] },
  { to: '/assistant', label: 'HR Assistant', icon: '💬', roles: 'all' },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const items = NAV.filter((n) => n.roles === 'all' || n.roles.includes(user?.role))

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside
        className={`fixed lg:static z-30 inset-y-0 left-0 w-64 bg-white border-r border-slate-200
          transform transition-transform ${open ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}
      >
        <div className="h-16 flex items-center gap-2 px-5 border-b border-slate-200">
          <span className="text-2xl">🤖</span>
          <span className="font-bold text-brand-700">FWC HRMS</span>
        </div>
        <nav className="p-3 space-y-1">
          {items.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium ${
                  isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100'
                }`
              }
            >
              <span>{n.icon}</span> {n.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {open && (
        <div className="fixed inset-0 bg-black/30 z-20 lg:hidden" onClick={() => setOpen(false)} />
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 lg:px-6">
          <button className="lg:hidden btn-ghost px-2 py-1" onClick={() => setOpen(true)}>☰</button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-sm font-semibold">{user?.full_name}</div>
              <div className="text-xs text-slate-500">{ROLE_LABELS[user?.role]}</div>
            </div>
            <div className="w-9 h-9 rounded-full bg-brand-600 text-white grid place-items-center font-semibold">
              {user?.full_name?.[0]}
            </div>
            <button className="btn-ghost text-sm" onClick={handleLogout}>Logout</button>
          </div>
        </header>
        <main className="flex-1 p-4 lg:p-6 max-w-7xl w-full mx-auto">{children}</main>
      </div>
    </div>
  )
}
