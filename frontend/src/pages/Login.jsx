import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const DEMO = [
  { role: 'Management Admin', email: 'admin@fwc.co.in', pass: 'admin123' },
  { role: 'Senior Manager', email: 'manager@fwc.co.in', pass: 'manager123' },
  { role: 'HR Recruiter', email: 'recruiter@fwc.co.in', pass: 'recruiter123' },
  { role: 'Employee', email: 'employee@fwc.co.in', pass: 'employee123' },
]

export default function Login() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('admin@fwc.co.in')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) navigate('/')

  async function submit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await login(email, password)
      navigate('/')
    } catch {
      setError('Invalid email or password')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Brand panel */}
      <div className="hidden lg:flex flex-col justify-center px-12 bg-gradient-to-br from-brand-600 to-brand-700 text-white">
        <div className="text-4xl font-bold flex items-center gap-3">🤖 FWC AI HRMS</div>
        <p className="mt-4 text-brand-50 text-lg max-w-md">
          Next-generation Human Resource Management, powered by AI: autonomous resume
          screening, voice screening, an HR assistant, and performance insights.
        </p>
        <ul className="mt-8 space-y-2 text-brand-100 text-sm">
          <li>✨ Autonomous AI resume screening &amp; ranking</li>
          <li>🎙️ AI voice screening interviews</li>
          <li>💬 RAG-powered HR assistant</li>
          <li>📈 AI performance &amp; attrition insights</li>
        </ul>
      </div>

      {/* Form */}
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <h1 className="text-2xl font-bold mb-1">Sign in</h1>
          <p className="text-slate-500 text-sm mb-6">Welcome back to FWC HRMS</p>
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Email</label>
              <input className="input mt-1" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">Password</label>
              <input
                type="password" className="input mt-1" value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {error && <div className="text-rose-600 text-sm">{error}</div>}
            <button className="btn-primary w-full" disabled={busy}>
              {busy ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6">
            <div className="text-xs uppercase text-slate-400 mb-2">Demo accounts</div>
            <div className="grid grid-cols-2 gap-2">
              {DEMO.map((d) => (
                <button
                  key={d.email}
                  onClick={() => { setEmail(d.email); setPassword(d.pass) }}
                  className="text-left text-xs border border-slate-200 rounded-lg p-2 hover:bg-slate-50"
                >
                  <div className="font-semibold text-slate-700">{d.role}</div>
                  <div className="text-slate-400 truncate">{d.email}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
