import { useEffect, useState } from 'react'
import api from '../api/client'
import { Badge, EmptyState, PageHeader, Spinner } from '../components/ui'

export default function Attendance() {
  const [records, setRecords] = useState([])
  const [leaves, setLeaves] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState('')
  const [leaveForm, setLeaveForm] = useState({ start_date: '', end_date: '', leave_type: 'casual', reason: '' })

  function load() {
    Promise.all([api.get('/api/attendance/me'), api.get('/api/attendance/leave/me')])
      .then(([a, l]) => { setRecords(a.data); setLeaves(l.data) })
      .finally(() => setLoading(false))
  }
  useEffect(() => { load() }, []) // eslint-disable-line

  const today = records.find((r) => r.date === new Date().toISOString().slice(0, 10))

  async function action(path) {
    setMsg('')
    try {
      await api.post(`/api/attendance/${path}`)
      setMsg(path === 'check-in' ? 'Checked in ✓' : 'Checked out ✓')
      load()
    } catch (e) { setMsg(e.response?.data?.detail || 'Error') }
  }

  async function requestLeave() {
    setMsg('')
    try {
      const { data } = await api.post('/api/attendance/leave', leaveForm)
      setMsg(`Leave ${data.status} (${data.days} day(s))`)
      setLeaveForm({ start_date: '', end_date: '', leave_type: 'casual', reason: '' })
      load()
    } catch (e) { setMsg(e.response?.data?.detail || 'Error') }
  }

  if (loading) return <Spinner />

  return (
    <div>
      <PageHeader title="Attendance & Leave" subtitle="Check in/out and manage leave" />
      {msg && <div className="mb-4 text-sm bg-brand-50 text-brand-700 px-3 py-2 rounded-lg">{msg}</div>}

      <div className="grid lg:grid-cols-3 gap-4 mb-6">
        <div className="card lg:col-span-1">
          <h3 className="font-semibold mb-2">Today</h3>
          <p className="text-sm text-slate-500 mb-3">
            {today?.check_in ? `In: ${new Date(today.check_in).toLocaleTimeString()}` : 'Not checked in'}
            {today?.check_out ? ` · Out: ${new Date(today.check_out).toLocaleTimeString()}` : ''}
          </p>
          <div className="flex gap-2">
            <button className="btn-primary flex-1" disabled={!!today?.check_in} onClick={() => action('check-in')}>Check in</button>
            <button className="btn-ghost flex-1" disabled={!today?.check_in || !!today?.check_out} onClick={() => action('check-out')}>Check out</button>
          </div>
        </div>

        <div className="card lg:col-span-2">
          <h3 className="font-semibold mb-3">Request leave</h3>
          <div className="grid sm:grid-cols-2 gap-3">
            <input type="date" className="input" value={leaveForm.start_date} onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })} />
            <input type="date" className="input" value={leaveForm.end_date} onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })} />
            <select className="input" value={leaveForm.leave_type} onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value })}>
              <option value="casual">Casual</option><option value="sick">Sick</option><option value="earned">Earned</option>
            </select>
            <input className="input" placeholder="Reason" value={leaveForm.reason} onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })} />
          </div>
          <button className="btn-primary mt-3" disabled={!leaveForm.start_date || !leaveForm.end_date} onClick={requestLeave}>Submit</button>
          <p className="text-xs text-slate-400 mt-2">Leaves up to 3 days auto-approve; longer ones need manager approval.</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-0">
          <h3 className="font-semibold p-4 pb-2">Recent attendance</h3>
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-left">
              <tr><th className="px-4 py-2">Date</th><th className="px-4 py-2">Status</th><th className="px-4 py-2">Hours</th></tr>
            </thead>
            <tbody>
              {records.slice(0, 12).map((r) => (
                <tr key={r.id} className="border-t border-slate-100">
                  <td className="px-4 py-2">{r.date}</td>
                  <td className="px-4 py-2"><Badge value={r.status} /></td>
                  <td className="px-4 py-2">{r.hours_worked || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!records.length && <EmptyState>No records.</EmptyState>}
        </div>

        <div className="card p-0">
          <h3 className="font-semibold p-4 pb-2">My leave requests</h3>
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-left">
              <tr><th className="px-4 py-2">From</th><th className="px-4 py-2">To</th><th className="px-4 py-2">Type</th><th className="px-4 py-2">Status</th></tr>
            </thead>
            <tbody>
              {leaves.map((l) => (
                <tr key={l.id} className="border-t border-slate-100">
                  <td className="px-4 py-2">{l.start_date}</td><td className="px-4 py-2">{l.end_date}</td>
                  <td className="px-4 py-2 capitalize">{l.leave_type}</td><td className="px-4 py-2"><Badge value={l.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          {!leaves.length && <EmptyState>No leave requests.</EmptyState>}
        </div>
      </div>
    </div>
  )
}
