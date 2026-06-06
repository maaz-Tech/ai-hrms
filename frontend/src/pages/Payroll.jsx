import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { EmptyState, PageHeader, Spinner } from '../components/ui'

const MONTHS = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const fmt = (n) => '₹' + Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })

export default function Payroll() {
  const { user } = useAuth()
  const canRun = ['management_admin', 'senior_manager', 'hr_recruiter'].includes(user.role)
  const [slips, setSlips] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState('')
  const now = new Date()
  const [run, setRun] = useState({ month: now.getMonth() + 1, year: now.getFullYear() })

  function load() {
    api.get('/api/payroll/me').then((r) => setSlips(r.data)).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, []) // eslint-disable-line

  async function runPayroll() {
    setMsg('')
    try {
      const { data } = await api.post('/api/payroll/run', run)
      setMsg(`Generated ${data.generated} payslips for ${MONTHS[data.month]} ${data.year}`)
      load()
    } catch (e) { setMsg(e.response?.data?.detail || 'Error') }
  }

  async function download(id) {
    const res = await api.get(`/api/payroll/${id}/pdf`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url; a.download = `payslip_${id}.pdf`; a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) return <Spinner />

  return (
    <div>
      <PageHeader title="Payroll" subtitle="Your payslips" />
      {msg && <div className="mb-4 text-sm bg-brand-50 text-brand-700 px-3 py-2 rounded-lg">{msg}</div>}

      {canRun && (
        <div className="card mb-6 flex flex-wrap items-end gap-3">
          <div>
            <label className="text-xs text-slate-500">Month</label>
            <select className="input" value={run.month} onChange={(e) => setRun({ ...run, month: +e.target.value })}>
              {MONTHS.slice(1).map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500">Year</label>
            <input type="number" className="input w-28" value={run.year} onChange={(e) => setRun({ ...run, year: +e.target.value })} />
          </div>
          <button className="btn-primary" onClick={runPayroll}>Run payroll</button>
          <span className="text-xs text-slate-400">Generates payslips for all active employees.</span>
        </div>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {slips.map((s) => (
          <div key={s.id} className="card">
            <div className="flex justify-between items-center mb-3">
              <div className="font-semibold">{MONTHS[s.month]} {s.year}</div>
              <span className="badge bg-emerald-100 text-emerald-700">{s.status}</span>
            </div>
            <Row label="Basic" v={s.basic} /><Row label="HRA" v={s.hra} />
            <Row label="Allowances" v={s.allowances} /><Row label="Deductions" v={-s.deductions} />
            <div className="border-t border-slate-200 mt-2 pt-2 flex justify-between font-bold">
              <span>Net pay</span><span className="text-brand-600">{fmt(s.net_pay)}</span>
            </div>
            <button className="btn-ghost w-full mt-3 text-sm" onClick={() => download(s.id)}>⬇ Download PDF</button>
          </div>
        ))}
      </div>
      {!slips.length && <EmptyState>No payslips yet.</EmptyState>}
    </div>
  )
}

const Row = ({ label, v }) => (
  <div className="flex justify-between text-sm py-0.5">
    <span className="text-slate-500">{label}</span><span>{fmt(v)}</span>
  </div>
)
