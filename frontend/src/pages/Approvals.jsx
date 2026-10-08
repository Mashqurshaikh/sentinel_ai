import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, X, Clock, Sparkles, AlertTriangle } from 'lucide-react'
import TopBar from '../components/TopBar'
import RiskBadge from '../components/RiskBadge'
import ProviderSelector from '../components/ProviderSelector'
import { getApprovals, approveRequest, rejectRequest } from '../api/client'
import { useAuth } from '../auth/AuthContext'

const TABS = [
  { key: 'pending', label: 'Pending' },
  { key: 'approved', label: 'Approved' },
  { key: 'rejected', label: 'Rejected' },
]

export default function Approvals() {
  const { user } = useAuth()
  const [tab, setTab] = useState('pending')
  const [items, setItems] = useState([])
  const [provider, setProvider] = useState(null)
  const [busyId, setBusyId] = useState(null)
  const [responses, setResponses] = useState({}) // id -> { llm_response, llm_error, llm_provider }

  const load = () => getApprovals(tab).then(setItems).catch(() => {})

  useEffect(() => { load() }, [tab])

  const decide = async (id, action) => {
    setBusyId(id)
    try {
      if (action === 'approve') {
        const res = await approveRequest(id, user.username, provider)
        if (res.llm_response || res.llm_error) {
          setResponses(prev => ({ ...prev, [id]: res }))
        }
      } else {
        await rejectRequest(id, user.username)
      }
      load()
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div>
      <TopBar title="Approval queue" subtitle="Blocked high-risk requests waiting for a human decision" />

      <div className="px-5 md:px-10 py-8 max-w-5xl">
        <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
          <div className="flex gap-2">
            {TABS.map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition ${
                  tab === t.key ? 'border-brand text-brand bg-brand/10' : 'border-line text-muted hover:text-ink'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <p className="text-xs text-muted font-mono">reviewing as {user.username}</p>
        </div>

        {tab === 'pending' && (
          <div className="mb-6 max-w-md">
            <ProviderSelector value={provider} onChange={setProvider} />
          </div>
        )}

        {items.length === 0 && (
          <div className="rounded-xl border border-dashed border-line py-16 text-center text-muted">
            <Clock size={24} className="mx-auto mb-3 opacity-50" />
            <p className="text-sm">No {tab} requests.</p>
          </div>
        )}

        <div className="flex flex-col gap-3">
          <AnimatePresence>
            {items.map(item => {
              const liveResponse = responses[item.id]
              const savedResponse = item.llm_response ? { llm_response: item.llm_response, llm_provider: item.llm_provider } : null
              const shown = liveResponse || savedResponse

              return (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, height: 0 }}
                  className="rounded-xl border border-line bg-surface p-5"
                >
                  <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                    <div className="flex items-center gap-3">
                      <RiskBadge level={item.risk_level} />
                      <span className="text-sm font-mono text-ink">{item.user_id}</span>
                      <span className="text-xs text-muted">{item.department}</span>
                    </div>
                    <span className="text-xs text-muted font-mono">{new Date(item.timestamp).toLocaleString()}</span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {item.threat_types.map(t => (
                      <span key={t} className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-2 border border-line text-muted">{t}</span>
                    ))}
                  </div>

                  <p className="text-xs text-muted font-mono mb-1">why it was blocked</p>
                  <ul className="text-sm mb-3 space-y-0.5">
                    {item.reasons.map((r, i) => <li key={i} className="text-ink">– {r}</li>)}
                  </ul>

                  <p className="text-xs text-muted font-mono mb-1">sanitized version (what would be sent if approved)</p>
                  <pre className="whitespace-pre-wrap text-sm font-mono bg-surface-2 border border-line rounded-lg px-3 py-2 text-ink mb-3">{item.sanitized_prompt}</pre>

                  {shown?.llm_response && (
                    <div className="mb-3">
                      <p className="text-xs text-muted font-mono mb-1 flex items-center gap-1.5">
                        <Sparkles size={12} className="text-brand" /> response from {shown.llm_provider}
                      </p>
                      <div className="whitespace-pre-wrap text-sm bg-brand/5 border border-brand/20 rounded-lg px-3 py-2 text-ink">{shown.llm_response}</div>
                    </div>
                  )}
                  {liveResponse?.llm_error && (
                    <div className="flex items-start gap-2 text-xs text-warn bg-warn/10 border border-warn/25 rounded-lg px-3 py-2 mb-3">
                      <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                      <span>{liveResponse.llm_error}</span>
                    </div>
                  )}

                  {item.status === 'pending' ? (
                    <div className="flex gap-2">
                      <motion.button
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => decide(item.id, 'approve')}
                        disabled={busyId === item.id}
                        className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-safe/10 border border-safe text-safe font-semibold px-4 py-2 text-sm hover:bg-safe/20 transition disabled:opacity-50"
                      >
                        <Check size={15} /> {provider ? `Approve & send to ${provider}` : 'Approve sanitized version'}
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => decide(item.id, 'reject')}
                        disabled={busyId === item.id}
                        className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-danger/10 border border-danger text-danger font-semibold px-4 py-2 text-sm hover:bg-danger/20 transition disabled:opacity-50"
                      >
                        <X size={15} /> Reject
                      </motion.button>
                    </div>
                  ) : (
                    <p className="text-xs text-muted italic">
                      {item.status === 'approved' ? 'Approved' : 'Rejected'} by {item.decided_by} on {new Date(item.decided_at).toLocaleString()}
                    </p>
                  )}
                </motion.div>
              )
            })}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
