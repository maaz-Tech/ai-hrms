import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { AiBadge, Badge, EmptyState, PageHeader, Spinner } from '../components/ui'

export default function Performance() {
  const { user } = useAuth()
  const isManager = ['management_admin', 'senior_manager'].includes(user.role)
  const [goals, setGoals] = useState([])
  const [loading, setLoading] = useState(true)
  const [newGoal, setNewGoal] = useState('')

  function load() {
    api.get('/api/performance/goals/me').then((r) => setGoals(r.data)).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, []) // eslint-disable-line

  async function addGoal() {
    if (!newGoal.trim()) return
    await api.post('/api/performance/goals', { title: newGoal })
    setNewGoal(''); load()
  }
  async function setProgress(g, progress) {
    await api.patch(`/api/performance/goals/${g.id}`, { progress })
    load()
  }

  if (loading) return <Spinner />

  return (
    <div>
      <PageHeader title="Performance" subtitle="Goals, progress and AI reviews" />

      <div className="card mb-6">
        <h3 className="font-semibold mb-3">My goals</h3>
        <div className="flex gap-2 mb-4">
          <input className="input" placeholder="Add a new goal…" value={newGoal}
            onChange={(e) => setNewGoal(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && addGoal()} />
          <button className="btn-primary" onClick={addGoal}>Add</button>
        </div>
        <div className="space-y-4">
          {goals.map((g) => (
            <div key={g.id}>
              <div className="flex justify-between items-center text-sm mb-1">
                <span className="font-medium">{g.title}</span>
                <Badge value={g.status} />
              </div>
              <div className="flex items-center gap-3">
                <input type="range" min="0" max="100" value={g.progress}
                  onChange={(e) => setProgress(g, +e.target.value)} className="flex-1" />
                <span className="text-sm text-slate-500 w-10">{g.progress}%</span>
              </div>
            </div>
          ))}
          {!goals.length && <EmptyState>No goals yet.</EmptyState>}
        </div>
      </div>

      {isManager && <TeamInsights />}
    </div>
  )
}

function TeamInsights() {
  const [emps, setEmps] = useState([])
  const [selected, setSelected] = useState('')
  const [insight, setInsight] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.get('/api/employees', { params: { limit: 200 } }).then((r) => setEmps(r.data))
  }, [])

  async function run() {
    if (!selected) return
    setBusy(true); setInsight(null)
    try {
      const { data } = await api.post(`/api/performance/insight/${selected}`)
      setInsight(data)
    } finally { setBusy(false) }
  }

  const riskColor = { low: 'text-emerald-600', medium: 'text-amber-600', high: 'text-rose-600' }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">AI Performance Insight & Attrition Risk</h3>
        {insight && <AiBadge powered={insight.ai_powered} />}
      </div>
      <div className="flex flex-wrap gap-2 mb-4">
        <select className="input max-w-xs" value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">Select an employee…</option>
          {emps.map((e) => <option key={e.id} value={e.id}>{e.full_name} — {e.job_title}</option>)}
        </select>
        <button className="btn-primary" disabled={!selected || busy} onClick={run}>
          {busy ? 'Analyzing…' : 'Generate insight'}
        </button>
      </div>

      {insight && (
        <div className="bg-slate-50 rounded-lg p-4">
          <div className="flex flex-wrap gap-4 items-center mb-3">
            <div className="text-sm">Rating: <span className="font-bold text-brand-600">{insight.rating}/5</span></div>
            <div className="text-sm">Attrition risk:{' '}
              <span className={`font-bold capitalize ${riskColor[insight.attrition_risk]}`}>{insight.attrition_risk}</span>
            </div>
          </div>
          <p className="text-sm text-slate-700 mb-3">{insight.summary}</p>
          <ul className="text-sm space-y-1">
            {insight.highlights.map((h, i) => <li key={i} className="flex gap-2"><span>•</span>{h}</li>)}
          </ul>
        </div>
      )}
    </div>
  )
}
