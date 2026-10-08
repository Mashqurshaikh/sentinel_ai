import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
  BarChart, Bar, Legend,
} from 'recharts'
import { Radio, Network, ListChecks, Megaphone, RefreshCw, Loader2, ClipboardCheck } from 'lucide-react'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import RiskBadge from '../components/RiskBadge'
import { useLiveFeed } from '../hooks/useLiveFeed'
import { getStats, getTimeseries, getDepartments, getAuditLogs, runAgent, getApprovals } from '../api/client'

const AGENTS = [
  { key: 'traffic-monitor', label: 'Traffic Monitor', icon: Network },
  { key: 'policy', label: 'Policy Agent', icon: ListChecks },
  { key: 'threat-intel', label: 'Threat Intel', icon: Megaphone },
  { key: 'data-pipeline', label: 'Data Pipeline', icon: RefreshCw },
]

export default function Dashboard() {
  const { events, connected } = useLiveFeed(20)
  const [stats, setStats] = useState(null)
  const [series, setSeries] = useState([])
  const [departments, setDepartments] = useState([])
  const [initialLogs, setInitialLogs] = useState([])
  const [pendingCount, setPendingCount] = useState(0)
  const [agentBusy, setAgentBusy] = useState(null)
  const [agentOutput, setAgentOutput] = useState(null)

  const refresh = () => {
    getStats().then(setStats).catch(() => {})
    getTimeseries(24).then(setSeries).catch(() => {})
    getDepartments().then(setDepartments).catch(() => {})
    getAuditLogs(20).then(setInitialLogs).catch(() => {})
    getApprovals('pending').then(rows => setPendingCount(rows.length)).catch(() => {})
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 15000)
    return () => clearInterval(interval)
  }, [])

  const feed = events.length > 0 ? events : initialLogs

  const handleAgent = async (key) => {
    setAgentBusy(key)
    setAgentOutput(null)
    try {
      const data = await runAgent(key)
      setAgentOutput({ key, data })
      refresh()
    } catch (e) {
      setAgentOutput({ key, error: e?.response?.data?.detail || 'Agent run failed.' })
    } finally {
      setAgentBusy(null)
    }
  }

  return (
    <div>
      <TopBar title="Admin dashboard" subtitle="Real-time traffic and threat visibility" live={connected} />

      <div className="px-5 md:px-10 py-8 flex flex-col gap-8 max-w-7xl">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard label="Total requests" value={stats?.total_requests ?? '—'} accent="brand" icon={Radio} />
          <StatCard label="Block rate" value={stats ? `${stats.block_rate}%` : '—'} accent="danger" />
          <StatCard label="File scans" value={stats?.file_scans ?? '—'} accent="info" />
          <StatCard label="Risk levels seen" value={stats ? Object.keys(stats.risk_distribution || {}).length : '—'} accent="safe" />
          <Link to="/approvals" className="block">
            <StatCard label="Pending approvals" value={pendingCount} accent={pendingCount > 0 ? 'danger' : 'safe'} icon={ClipboardCheck} sub={pendingCount > 0 ? 'needs review' : 'all clear'} />
          </Link>
        </div>

        <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6">
          <div className="rounded-xl border border-line bg-surface p-5">
            <h3 className="font-display font-semibold text-sm mb-4">Activity — last 24h by risk level</h3>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={series}>
                <defs>
                  <linearGradient id="highGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ff4d5e" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#ff4d5e" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="medGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ffb020" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#ffb020" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="lowGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#17d9a3" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#17d9a3" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#dde1e9" vertical={false} />
                <XAxis dataKey="time" tick={{ fill: '#5b6478', fontSize: 10 }} tickFormatter={t => new Date(t).getHours() + ':00'} axisLine={{ stroke: '#dde1e9' }} tickLine={false} />
                <YAxis tick={{ fill: '#5b6478', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #dde1e9', borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="high" stackId="1" stroke="#ff4d5e" fill="url(#highGrad)" />
                <Area type="monotone" dataKey="medium" stackId="1" stroke="#ffb020" fill="url(#medGrad)" />
                <Area type="monotone" dataKey="low" stackId="1" stroke="#17d9a3" fill="url(#lowGrad)" />
              </AreaChart>
            </ResponsiveContainer>
            {series.length === 0 && <p className="text-xs text-muted text-center mt-2">No activity yet — scan a few prompts in the Gateway.</p>}
          </div>

          <div className="rounded-xl border border-line bg-surface p-5">
            <h3 className="font-display font-semibold text-sm mb-4">Requests by department</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={departments}>
                <CartesianGrid strokeDasharray="3 3" stroke="#dde1e9" vertical={false} />
                <XAxis dataKey="department" tick={{ fill: '#5b6478', fontSize: 10 }} axisLine={{ stroke: '#dde1e9' }} tickLine={false} />
                <YAxis tick={{ fill: '#5b6478', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #dde1e9', borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="total" fill="#4fb2ff" radius={[4, 4, 0, 0]} name="Total" />
                <Bar dataKey="blocked" fill="#ff4d5e" radius={[4, 4, 0, 0]} name="Blocked" />
              </BarChart>
            </ResponsiveContainer>
            {departments.length === 0 && <p className="text-xs text-muted text-center mt-2">No department data yet.</p>}
          </div>
        </div>

        <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6">
          <div className="rounded-xl border border-line bg-surface overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-line">
              <h3 className="font-display font-semibold text-sm">Live feed</h3>
              <span className="text-xs text-muted font-mono">{feed.length} events</span>
            </div>
            <div className="max-h-96 overflow-y-auto divide-y divide-line">
              {feed.length === 0 && <p className="text-sm text-muted px-5 py-8 text-center">Waiting for activity…</p>}
              {feed.map((e, i) => (
                <motion.div
                  key={e.id ?? i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-3 px-5 py-3 text-sm"
                >
                  <RiskBadge level={e.risk_level} />
                  <span className="font-mono text-xs text-ink flex-1 truncate">{e.user_id}</span>
                  <span className="text-xs text-muted hidden sm:inline">{e.department}</span>
                  <span className="text-xs text-muted font-mono">
                    {new Date(e.timestamp).toLocaleTimeString()}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-line bg-surface p-5">
            <h3 className="font-display font-semibold text-sm mb-4">Autonomous agents</h3>
            <div className="grid grid-cols-2 gap-2.5 mb-4">
              {AGENTS.map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => handleAgent(key)}
                  disabled={agentBusy === key}
                  className="flex flex-col items-center gap-1.5 rounded-lg border border-line px-3 py-3 text-xs hover:border-brand/50 hover:bg-surface-2 transition disabled:opacity-50"
                >
                  {agentBusy === key ? <Loader2 size={16} className="animate-spin text-brand" /> : <Icon size={16} className="text-brand" />}
                  {label}
                </button>
              ))}
            </div>
            {agentOutput && (
              <div className="rounded-lg bg-surface-2 border border-line p-3 max-h-56 overflow-y-auto">
                <p className="text-xs text-muted font-mono mb-1">{agentOutput.key}</p>
                <pre className="text-[11px] font-mono text-ink whitespace-pre-wrap break-words">
                  {JSON.stringify(agentOutput.error || agentOutput.data, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
