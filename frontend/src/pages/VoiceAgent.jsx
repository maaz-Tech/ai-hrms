import { useEffect, useRef, useState } from 'react'
import api from '../api/client'
import { AiBadge, PageHeader } from '../components/ui'

// Browser Web Speech API (free, no key) for STT + TTS.
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

export default function VoiceAgent() {
  const [jobTitle, setJobTitle] = useState('AI/ML Engineer')
  const [history, setHistory] = useState([]) // {role, content, score?}
  const [question, setQuestion] = useState('')
  const [listening, setListening] = useState(false)
  const [started, setStarted] = useState(false)
  const [finished, setFinished] = useState(false)
  const [scorecard, setScorecard] = useState(null)
  const [aiPowered, setAiPowered] = useState(false)
  const [interim, setInterim] = useState('')
  const recognitionRef = useRef(null)
  const supported = !!SpeechRecognition

  useEffect(() => () => speechSynthesis.cancel(), [])

  function speak(text) {
    if (!text) return
    speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.rate = 1
    speechSynthesis.speak(u)
  }

  async function sendTurn(transcript, hist) {
    const { data } = await api.post('/api/ai/voice/turn', {
      job_title: jobTitle, transcript, history: hist.map(({ role, content }) => ({ role, content })),
    })
    setAiPowered(data.ai_powered)
    if (data.finished) {
      setFinished(true); setScorecard(data.scorecard); setQuestion('')
      speak('Thank you, that concludes the screening.')
    } else {
      setQuestion(data.question)
      setHistory((h) => [...h, { role: 'assistant', content: data.question }])
      speak(data.question)
    }
    return data
  }

  async function start() {
    setStarted(true); setFinished(false); setScorecard(null); setHistory([])
    await sendTurn('', [])
  }

  function listen() {
    if (!supported) return
    const rec = new SpeechRecognition()
    rec.lang = 'en-US'; rec.interimResults = true; rec.continuous = false
    let finalText = ''
    rec.onresult = (e) => {
      let interimText = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript
        if (e.results[i].isFinal) finalText += t
        else interimText += t
      }
      setInterim(interimText)
    }
    rec.onend = async () => {
      setListening(false); setInterim('')
      const answer = finalText.trim()
      if (!answer) return
      const newHist = [...history, { role: 'user', content: answer }]
      setHistory(newHist)
      await sendTurn(answer, newHist)
    }
    rec.onerror = () => setListening(false)
    recognitionRef.current = rec
    setListening(true)
    rec.start()
  }

  function stopListening() {
    recognitionRef.current?.stop()
  }

  return (
    <div>
      <PageHeader title="AI Voice Screening Agent" subtitle="Conversational, voice-driven candidate screening">
        {started && <AiBadge powered={aiPowered} />}
      </PageHeader>

      {!supported && (
        <div className="card mb-4 bg-amber-50 border-amber-200 text-amber-700 text-sm">
          Your browser doesn't support the Web Speech API. Use Chrome/Edge for the full voice experience.
          You can still read the questions and type answers below.
        </div>
      )}

      {!started ? (
        <div className="card max-w-lg">
          <label className="text-sm font-medium">Role being screened for</label>
          <input className="input mt-1 mb-4" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />
          <button className="btn-primary" onClick={start}>🎙️ Start voice screening</button>
          <p className="text-xs text-slate-400 mt-3">
            The AI agent asks questions aloud, listens to spoken answers, scores them and produces a scorecard.
          </p>
        </div>
      ) : (
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 card">
            <div className="min-h-[300px] space-y-3">
              {history.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'assistant' ? 'justify-start' : 'justify-end'}`}>
                  <div className={`max-w-md px-4 py-2 rounded-2xl text-sm ${
                    m.role === 'assistant' ? 'bg-slate-100' : 'bg-brand-600 text-white'}`}>
                    {m.content}
                  </div>
                </div>
              ))}
              {interim && <div className="text-right text-slate-400 text-sm italic">{interim}…</div>}
            </div>

            {!finished ? (
              <div className="border-t border-slate-200 pt-4 mt-4 flex items-center gap-3">
                {!listening ? (
                  <button className="btn-primary" disabled={!question} onClick={listen}>🎤 Answer</button>
                ) : (
                  <button className="btn bg-rose-500 text-white animate-pulse" onClick={stopListening}>⏹ Stop & submit</button>
                )}
                <button className="btn-ghost text-sm" disabled={!question} onClick={() => speak(question)}>🔊 Repeat question</button>
                <TypeFallback question={question} onSubmit={async (txt) => {
                  const nh = [...history, { role: 'user', content: txt }]
                  setHistory(nh); await sendTurn(txt, nh)
                }} />
              </div>
            ) : (
              <div className="border-t border-slate-200 pt-4 mt-4">
                <button className="btn-primary" onClick={start}>↻ Screen another candidate</button>
              </div>
            )}
          </div>

          <div className="card">
            <h3 className="font-semibold mb-3">Scorecard</h3>
            {scorecard ? (
              <div className="space-y-2">
                <div className="text-center py-4">
                  <div className="text-5xl font-bold text-brand-600">{scorecard.overall_score}</div>
                  <div className="text-sm text-slate-400">/ 10 overall</div>
                </div>
                <div className="flex justify-between text-sm"><span>Answers given</span><b>{scorecard.answers_given}</b></div>
                <div className="flex justify-between text-sm"><span>Recommendation</span>
                  <span className={`font-bold ${scorecard.recommendation === 'PROCEED' ? 'text-emerald-600' : 'text-amber-600'}`}>
                    {scorecard.recommendation}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-400">The scorecard appears when the interview concludes.</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function TypeFallback({ question, onSubmit }) {
  const [text, setText] = useState('')
  return (
    <div className="flex-1 flex gap-2">
      <input className="input" placeholder="…or type your answer" value={text}
        disabled={!question} onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && text.trim()) { onSubmit(text); setText('') } }} />
    </div>
  )
}
