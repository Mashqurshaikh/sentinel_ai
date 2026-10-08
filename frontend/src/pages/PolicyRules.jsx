import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Trash2, ToggleLeft, ToggleRight, AlertCircle } from 'lucide-react'
import TopBar from '../components/TopBar'
import { getRules, createRule, deleteRule, toggleRule } from '../api/client'

const SEVERITIES = ['medium', 'high', 'critical']

export default function PolicyRules() {
  const [rules, setRules] = useState([])
  const [name, setName] = useState('')
  const [pattern, setPattern] = useState('')
  const [severity, setSeverity] = useState('high')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const load = () => getRules().then(setRules).catch(() => {})

  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim() || !pattern.trim()) return
    setSaving(true)
    setError('')
    try {
      await createRule(name.trim(), pattern.trim(), severity)
      setName('')
      setPattern('')
      setSeverity('high')
      load()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not save that rule.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    await deleteRule(id)
    load()
  }

  const handleToggle = async (id, active) => {
    await toggleRule(id, !active)
    load()
  }

  return (
    <div>
      <TopBar title="Policy rules" subtitle="Custom detection patterns, on top of the built-in rule set" />

      <div className="px-5 md:px-10 py-8 grid lg:grid-cols-[1fr_1.3fr] gap-8 max-w-6xl">
        <form onSubmit={handleCreate} className="rounded-xl border border-line bg-surface p-5 flex flex-col gap-4 h-fit">
          <h3 className="font-display font-semibold text-sm">Add a rule</h3>
          <div>
            <label className="text-xs text-muted font-mono block mb-1">rule name</label>
            <input
              value={name}
              onChange={e => setName(e.target.value.toUpperCase().replace(/\s+/g, '_'))}
              placeholder="INTERNAL_TICKET_ID"
              className="w-full rounded-lg bg-surface-2 border border-line px-3 py-2 text-sm font-mono focus:outline-none focus:border-brand"
            />
          </div>
          <div>
            <label className="text-xs text-muted font-mono block mb-1">regex pattern</label>
            <input
              value={pattern}
              onChange={e => setPattern(e.target.value)}
              placeholder="TICKET-[0-9]{5}"
              className="w-full rounded-lg bg-surface-2 border border-line px-3 py-2 text-sm font-mono focus:outline-none focus:border-brand"
            />
          </div>
          <div>
            <label className="text-xs text-muted font-mono block mb-1">severity</label>
            <div className="flex gap-2">
              {SEVERITIES.map(s => (
                <button
                  type="button"
                  key={s}
                  onClick={() => setSeverity(s)}
                  className={`flex-1 rounded-lg border px-3 py-2 text-xs font-mono uppercase transition ${
                    severity === s ? 'border-brand text-brand bg-brand/10' : 'border-line text-muted hover:text-ink'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
          {error && (
            <p className="text-xs text-danger flex items-center gap-1.5"><AlertCircle size={13} /> {error}</p>
          )}
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand text-onbrand font-semibold px-4 py-2.5 text-sm hover:brightness-110 transition disabled:opacity-50"
          >
            <Plus size={15} /> {saving ? 'Saving…' : 'Add rule'}
          </button>
          <p className="text-xs text-muted leading-relaxed">
            Custom rules run alongside the built-in secret scanner on every prompt and file scan.
            A match immediately raises the risk level for that severity tier.
          </p>
        </form>

        <div className="rounded-xl border border-line bg-surface overflow-hidden h-fit">
          <div className="px-5 py-4 border-b border-line flex items-center justify-between">
            <h3 className="font-display font-semibold text-sm">Active rule set</h3>
            <span className="text-xs text-muted font-mono">{rules.length} rules</span>
          </div>
          <div className="divide-y divide-line max-h-[520px] overflow-y-auto">
            {rules.length === 0 && (
              <p className="text-sm text-muted px-5 py-8 text-center">No custom rules yet. Add one on the left.</p>
            )}
            <AnimatePresence>
              {rules.map(rule => (
                <motion.div
                  key={rule.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0, height: 0 }}
                  className="flex items-center gap-3 px-5 py-3"
                >
                  <button onClick={() => handleToggle(rule.id, rule.active)} className="text-muted hover:text-brand shrink-0">
                    {rule.active ? <ToggleRight size={22} className="text-safe" /> : <ToggleLeft size={22} />}
                  </button>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-mono text-ink truncate">{rule.name}</p>
                    <p className="text-xs font-mono text-muted truncate">{rule.pattern}</p>
                  </div>
                  <span className={`text-[10px] font-mono uppercase px-2 py-1 rounded shrink-0 ${
                    rule.severity === 'critical' ? 'bg-danger/10 text-danger' :
                    rule.severity === 'high' ? 'bg-warn/10 text-warn' : 'bg-info/10 text-info'
                  }`}>{rule.severity}</span>
                  <button onClick={() => handleDelete(rule.id)} className="text-muted hover:text-danger shrink-0">
                    <Trash2 size={16} />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}
