import { useEffect, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import api from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { EmptyState, PageHeader, Spinner, StatCard } from '../components/ui'

const PIE = ['#3b6fe0', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6']

export default function Dashboard() {
  const { user } = useAuth()
  const isStaff = ['management_admin', 'senior_manager', 'hr_recruiter'].includes(user.role)
  const [me, setMe] = useState(null)
  const [company, setCompany] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const calls = [api.get('/api/dashboard/me')]
    if (isStaff) calls.push(api.get('/api/dashboard/company'))
    Promise.all(calls)
      .then(([m, c]) => { setMe(m.data); if (c) setCompany(c.data) })
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line

  if (loading) return <Spinner />

  return (
    <div>
      <PageHeader
        title={`Welcome, ${user.full_name.split(' ')[0]} 👋`}
        subtitle="Here's your activity overview"
      />

      {/* Personal stats */}
      {me?.employee ? (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard label="Days present (month)" value={me.stats.days_present_this_month} accent="green" />
            <StatCard label="Open goals" value={me.stats.open_goals} accent="amber" />
            <StatCard label="Avg goal progress" value={`${me.stats.avg_goal_progress}%`} />
            <StatCard label="Leave balance" value={me.employee.leave_balance} sub="days" accent="brand" />
          </div>
          <div className="grid lg:grid-cols-2 gap-4 mb-6">
            <div className="card">
              <h3 className="font-semibold mb-3">My attendance hours</h3>
              {me.attendance_trend?.length ? (
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={me.attendance_trend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} hide />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="hours" stroke="#3b6fe0" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              ) : <EmptyState>No attendance yet — check in from the Attendance page.</EmptyState>}
            </div>
            <div className="card">
              <h3 className="font-semibold mb-3">My goals</h3>
              {me.goals?.length ? (
                <div className="space-y-3">
                  {me.goals.map((g, i) => (
                    <div key={i}>
                      <div className="flex justify-between text-sm">
                        <span className="truncate">{g.title}</span>
                        <span className="text-slate-500">{g.progress}%</span>
                      </div>
                      <div className="h-2 bg-slate-100 rounded-full mt-1">
                        <div className="h-2 bg-brand-500 rounded-full" style={{ width: `${g.progress}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : <EmptyState>No goals set.</EmptyState>}
            </div>
          </div>
        </>
      ) : (
        <div className="card mb-6 text-slate-500">No employee profile linked to this account.</div>
      )}

      {/* Company-wide (staff only) */}
      {company?.totals && (
        <>
          <h2 className="text-lg font-bold mb-3 mt-8">Company Overview</h2>
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
            <StatCard label="Active employees" value={company.totals.active_employees} />
            <StatCard label="Present today" value={company.totals.present_today} accent="green" />
            <StatCard label="Open jobs" value={company.totals.open_jobs} accent="amber" />
            <StatCard label="Applications" value={company.totals.total_applications} />
            <StatCard label="AI shortlisted" value={company.totals.shortlisted_candidates} accent="green" />
            <StatCard label="Pending leaves" value={company.totals.pending_leave_requests} accent="rose" />
          </div>
          <div className="grid lg:grid-cols-2 gap-4">
            <div className="card">
              <h3 className="font-semibold mb-3">Headcount by department</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={company.headcount_by_department}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="department" tick={{ fontSize: 11 }} interval={0} angle={-15} height={50} />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {company.headcount_by_department.map((_, i) => (
                      <Cell key={i} fill={PIE[i % PIE.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <h3 className="font-semibold mb-3">Recruitment funnel</h3>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={company.application_funnel.filter((s) => s.count > 0)}
                    dataKey="count" nameKey="stage" cx="50%" cy="50%" outerRadius={90} label
                  >
                    {company.application_funnel.map((_, i) => (
                      <Cell key={i} fill={PIE[i % PIE.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
