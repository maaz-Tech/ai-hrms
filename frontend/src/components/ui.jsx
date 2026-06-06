// Small reusable presentational components.

export function Spinner({ label = 'Loading…' }) {
  return (
    <div className="flex items-center gap-3 text-slate-500 py-8 justify-center">
      <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      {label}
    </div>
  )
}

export function StatCard({ label, value, sub, accent = 'brand' }) {
  const colors = {
    brand: 'text-brand-600', green: 'text-emerald-600',
    amber: 'text-amber-600', rose: 'text-rose-600',
  }
  return (
    <div className="card">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`text-3xl font-bold mt-1 ${colors[accent] || colors.brand}`}>{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  )
}

const STATUS_COLORS = {
  shortlisted: 'bg-emerald-100 text-emerald-700',
  hired: 'bg-emerald-100 text-emerald-700',
  screened: 'bg-blue-100 text-blue-700',
  new: 'bg-slate-100 text-slate-600',
  rejected: 'bg-rose-100 text-rose-700',
  approved: 'bg-emerald-100 text-emerald-700',
  pending: 'bg-amber-100 text-amber-700',
  present: 'bg-emerald-100 text-emerald-700',
  wfh: 'bg-indigo-100 text-indigo-700',
  leave: 'bg-amber-100 text-amber-700',
  absent: 'bg-rose-100 text-rose-700',
  STRONG_YES: 'bg-emerald-100 text-emerald-700',
  YES: 'bg-teal-100 text-teal-700',
  MAYBE: 'bg-amber-100 text-amber-700',
  NO: 'bg-rose-100 text-rose-700',
}

export function Badge({ value }) {
  const cls = STATUS_COLORS[value] || 'bg-slate-100 text-slate-600'
  return <span className={`badge ${cls}`}>{String(value).replace(/_/g, ' ')}</span>
}

export function EmptyState({ children }) {
  return <div className="text-center text-slate-400 py-10">{children}</div>
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">{title}</h1>
        {subtitle && <p className="text-slate-500 text-sm mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}

export function AiBadge({ powered }) {
  return (
    <span
      className={`badge ${powered ? 'bg-violet-100 text-violet-700' : 'bg-slate-100 text-slate-500'}`}
      title={powered ? 'Powered by Gemini' : 'Heuristic mode — set GEMINI_API_KEY for full AI'}
    >
      {powered ? '✨ AI (Gemini)' : '⚙ Heuristic mode'}
    </span>
  )
}
