import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Badge, EmptyState, PageHeader, Spinner } from '../components/ui'

export default function Employees() {
  const { user } = useAuth()
  const canEdit = ['management_admin', 'senior_manager', 'hr_recruiter'].includes(user.role)
  const [rows, setRows] = useState([])
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  function load() {
    setLoading(true)
    api.get('/api/employees', { params: { q: q || undefined } })
      .then((r) => setRows(r.data))
      .finally(() => setLoading(false))
  }
  useEffect(() => { load() }, []) // eslint-disable-line

  return (
    <div>
      <PageHeader title="Employees" subtitle={`${rows.length} shown`}>
        {canEdit && (
          <button className="btn-primary" onClick={() => setShowForm((s) => !s)}>
            {showForm ? 'Close' : '+ Add Employee'}
          </button>
        )}
      </PageHeader>

      {showForm && <AddEmployee onDone={() => { setShowForm(false); load() }} />}

      <div className="flex gap-2 mb-4">
        <input
          className="input max-w-xs" placeholder="Search name, email, code…"
          value={q} onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && load()}
        />
        <button className="btn-ghost" onClick={load}>Search</button>
      </div>

      {loading ? <Spinner /> : (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-left">
              <tr>
                <th className="px-4 py-3">Code</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3 hidden md:table-cell">Department</th>
                <th className="px-4 py-3 hidden md:table-cell">Location</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((e) => (
                <tr key={e.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono text-xs">{e.employee_code}</td>
                  <td className="px-4 py-3 font-medium">{e.full_name}<div className="text-xs text-slate-400">{e.email}</div></td>
                  <td className="px-4 py-3">{e.job_title}</td>
                  <td className="px-4 py-3 hidden md:table-cell">{e.department_name || '—'}</td>
                  <td className="px-4 py-3 hidden md:table-cell">{e.location || '—'}</td>
                  <td className="px-4 py-3"><Badge value={e.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          {!rows.length && <EmptyState>No employees found.</EmptyState>}
        </div>
      )}
    </div>
  )
}

function AddEmployee({ onDone }) {
  const [form, setForm] = useState({ full_name: '', email: '', job_title: '', location: 'Bangalore', base_salary: 1000000 })
  const [err, setErr] = useState('')
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function save() {
    setErr('')
    try {
      await api.post('/api/employees', { ...form, base_salary: Number(form.base_salary) })
      onDone()
    } catch (e) {
      setErr(e.response?.data?.detail || 'Failed to create')
    }
  }
  return (
    <div className="card mb-4 grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <input className="input" placeholder="Full name" value={form.full_name} onChange={set('full_name')} />
      <input className="input" placeholder="Email" value={form.email} onChange={set('email')} />
      <input className="input" placeholder="Job title" value={form.job_title} onChange={set('job_title')} />
      <input className="input" placeholder="Location" value={form.location} onChange={set('location')} />
      <input className="input" placeholder="Base salary" type="number" value={form.base_salary} onChange={set('base_salary')} />
      <button className="btn-primary" onClick={save}>Save</button>
      {err && <div className="text-rose-600 text-sm col-span-full">{err}</div>}
    </div>
  )
}
