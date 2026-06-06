import { useEffect, useState } from 'react'
import api from '../api/client'
import { AiBadge, Badge, EmptyState, PageHeader, Spinner } from '../components/ui'

export default function Recruitment() {
  const [jobs, setJobs] = useState([])
  const [active, setActive] = useState(null)
  const [apps, setApps] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingApps, setLoadingApps] = useState(false)

  function loadJobs() {
    api.get('/api/recruitment/jobs').then((r) => {
      setJobs(r.data)
      if (r.data.length && !active) selectJob(r.data[0])
    }).finally(() => setLoading(false))
  }
  useEffect(() => { loadJobs() }, []) // eslint-disable-line

  function selectJob(job) {
    setActive(job)
    setLoadingApps(true)
    api.get(`/api/recruitment/jobs/${job.id}/applications`)
      .then((r) => setApps(r.data)).finally(() => setLoadingApps(false))
  }

  async function rescreen() {
    setLoadingApps(true)
    const { data } = await api.post(`/api/recruitment/jobs/${active.id}/rescreen`)
    setApps(data); setLoadingApps(false)
  }

  if (loading) return <Spinner />

  return (
    <div>
      <PageHeader title="Recruitment" subtitle="Autonomous AI resume screening — candidates ranked with no human intervention" />
      <div className="grid lg:grid-cols-4 gap-4">
        {/* Jobs list */}
        <div className="lg:col-span-1 space-y-2">
          <NewJob onCreated={loadJobs} />
          {jobs.map((j) => (
            <button key={j.id} onClick={() => selectJob(j)}
              className={`w-full text-left card !p-3 ${active?.id === j.id ? 'ring-2 ring-brand-500' : ''}`}>
              <div className="font-medium text-sm">{j.title}</div>
              <div className="text-xs text-slate-400">{j.department} · {j.application_count} applicants</div>
            </button>
          ))}
        </div>

        {/* Applications */}
        <div className="lg:col-span-3">
          {active && (
            <div className="card">
              <div className="flex flex-wrap justify-between items-start gap-2 mb-3">
                <div>
                  <h3 className="font-bold">{active.title}</h3>
                  <p className="text-xs text-slate-500 max-w-xl">{active.requirements}</p>
                </div>
                <button className="btn-ghost text-sm" onClick={rescreen}>↻ Re-run AI screening</button>
              </div>

              <UploadResume jobId={active.id} onDone={() => selectJob(active)} />

              {loadingApps ? <Spinner /> : (
                <div className="overflow-x-auto mt-3">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 text-slate-500 text-left">
                      <tr>
                        <th className="px-3 py-2">Candidate</th>
                        <th className="px-3 py-2">AI Score</th>
                        <th className="px-3 py-2 hidden md:table-cell">Rec.</th>
                        <th className="px-3 py-2">Status</th>
                        <th className="px-3 py-2 hidden lg:table-cell">AI Reasoning</th>
                      </tr>
                    </thead>
                    <tbody>
                      {apps.map((a) => (
                        <tr key={a.id} className="border-t border-slate-100 align-top">
                          <td className="px-3 py-2 font-medium">{a.candidate_name}
                            <div className="text-xs text-slate-400">{a.candidate_email}</div>
                          </td>
                          <td className="px-3 py-2">
                            <ScoreBar score={a.ai_score} />
                          </td>
                          <td className="px-3 py-2 hidden md:table-cell">{a.recommendation && <Badge value={a.recommendation} />}</td>
                          <td className="px-3 py-2"><Badge value={a.status} /></td>
                          <td className="px-3 py-2 hidden lg:table-cell text-xs text-slate-500 max-w-xs">{a.reasoning}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!apps.length && <EmptyState>No applicants yet — upload a resume above.</EmptyState>}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ScoreBar({ score }) {
  if (score == null) return <span className="text-slate-400">—</span>
  const pct = (score / 10) * 100
  const color = score >= 7 ? 'bg-emerald-500' : score >= 5 ? 'bg-amber-500' : 'bg-rose-400'
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 bg-slate-100 rounded-full"><div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} /></div>
      <span className="font-semibold w-8">{score}</span>
    </div>
  )
}

function NewJob({ onCreated }) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ title: '', department: '', requirements: '' })
  async function create() {
    await api.post('/api/recruitment/jobs', form)
    setForm({ title: '', department: '', requirements: '' }); setOpen(false); onCreated()
  }
  if (!open) return <button className="btn-primary w-full mb-2" onClick={() => setOpen(true)}>+ New job posting</button>
  return (
    <div className="card !p-3 space-y-2 mb-2">
      <input className="input" placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
      <input className="input" placeholder="Department" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
      <textarea className="input" placeholder="Requirements (comma separated)" rows="3" value={form.requirements} onChange={(e) => setForm({ ...form, requirements: e.target.value })} />
      <div className="flex gap-2">
        <button className="btn-primary flex-1" onClick={create}>Create</button>
        <button className="btn-ghost" onClick={() => setOpen(false)}>Cancel</button>
      </div>
    </div>
  )
}

function UploadResume({ jobId, onDone }) {
  const [form, setForm] = useState({ candidate_name: '', candidate_email: '' })
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)

  async function upload() {
    if (!file || !form.candidate_name || !form.candidate_email) return
    setBusy(true); setResult(null)
    const fd = new FormData()
    fd.append('candidate_name', form.candidate_name)
    fd.append('candidate_email', form.candidate_email)
    fd.append('file', file)
    try {
      const { data } = await api.post(`/api/recruitment/jobs/${jobId}/upload`, fd)
      setResult(data)
      onDone()
    } finally { setBusy(false) }
  }

  return (
    <div className="bg-slate-50 rounded-lg p-3 mb-2">
      <div className="text-sm font-semibold mb-2">Upload résumé — auto-screened on submit</div>
      <div className="grid sm:grid-cols-3 gap-2">
        <input className="input" placeholder="Candidate name" value={form.candidate_name} onChange={(e) => setForm({ ...form, candidate_name: e.target.value })} />
        <input className="input" placeholder="Email" value={form.candidate_email} onChange={(e) => setForm({ ...form, candidate_email: e.target.value })} />
        <input type="file" accept=".pdf,.txt" className="input !py-1.5" onChange={(e) => setFile(e.target.files[0])} />
      </div>
      <button className="btn-primary mt-2 text-sm" disabled={busy} onClick={upload}>
        {busy ? 'Screening with AI…' : 'Upload & screen'}
      </button>
      {result && (
        <div className="mt-2 text-sm flex items-center gap-2">
          Screened: <Badge value={result.recommendation} /> score <b>{result.ai_score}</b> → <Badge value={result.status} />
        </div>
      )}
    </div>
  )
}
