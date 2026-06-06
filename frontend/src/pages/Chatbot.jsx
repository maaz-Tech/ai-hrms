import { useEffect, useRef, useState } from 'react'
import api from '../api/client'
import { AiBadge, PageHeader } from '../components/ui'

const SUGGESTIONS = [
  'How many leave days do I have left?',
  "What's the work from home policy?",
  'When am I eligible for ESOPs?',
  'How is my salary structured?',
]

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hi! I'm your FWC HR assistant. Ask me about leave, payroll, policies or your own details." },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [aiPowered, setAiPowered] = useState(null)
  const endRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function send(text) {
    const msg = (text ?? input).trim()
    if (!msg || busy) return
    const history = messages.filter((m) => m.role !== 'system')
    setMessages((m) => [...m, { role: 'user', content: msg }])
    setInput(''); setBusy(true)
    try {
      const { data } = await api.post('/api/ai/chat', { message: msg, history })
      setAiPowered(data.ai_powered)
      setMessages((m) => [...m, { role: 'assistant', content: data.reply, sources: data.sources }])
    } catch {
      setMessages((m) => [...m, { role: 'assistant', content: 'Sorry, something went wrong.' }])
    } finally { setBusy(false) }
  }

  return (
    <div>
      <PageHeader title="HR Assistant" subtitle="RAG-powered answers grounded in company policy + your data">
        {aiPowered !== null && <AiBadge powered={aiPowered} />}
      </PageHeader>

      <div className="card flex flex-col h-[70vh] p-0">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-lg px-4 py-2.5 rounded-2xl text-sm whitespace-pre-wrap ${
                m.role === 'user' ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-800'}`}>
                {m.content}
                {m.sources?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {m.sources.map((s, j) => (
                      <span key={j} className="badge bg-white/70 text-slate-500 border border-slate-200">📄 {s}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {busy && <div className="text-slate-400 text-sm">Assistant is typing…</div>}
          <div ref={endRef} />
        </div>

        {messages.length <= 1 && (
          <div className="px-4 pb-2 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="text-xs border border-slate-200 rounded-full px-3 py-1 hover:bg-slate-50"
                onClick={() => send(s)}>{s}</button>
            ))}
          </div>
        )}

        <div className="border-t border-slate-200 p-3 flex gap-2">
          <input className="input" placeholder="Ask a question…" value={input}
            onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && send()} />
          <button className="btn-primary" disabled={busy} onClick={() => send()}>Send</button>
        </div>
      </div>
    </div>
  )
}
