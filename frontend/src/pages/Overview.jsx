import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ShieldCheck, ScanLine as ScanIcon, Lock, Bot, ArrowRight } from 'lucide-react'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import { getStats } from '../api/client'

const PILLARS = [
  {
    icon: ScanIcon,
    title: 'Threat detection',
    text: 'Classifies every prompt for source code, secrets, and prompt-injection attempts before it leaves the building.',
  },
  {
    icon: Lock,
    title: 'Privacy engine',
    text: 'Finds and masks personal data — names, phone numbers, account IDs — using NLP entity recognition plus pattern rules.',
  },
  {
    icon: Bot,
    title: 'Autonomous agents',
    text: 'Four background agents watch traffic, tune policy, brief admins, and retrain the model without manual upkeep.',
  },
  {
    icon: ShieldCheck,
    title: 'Compliance mapping',
    text: 'Every flagged item is tagged against GDPR, PCI-DSS, SOC 2, and India\u2019s DPDP Act for audit-ready reporting.',
  },
]

export default function Overview() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    getStats().then(setStats).catch(() => {})
  }, [])

  return (
    <div>
      <TopBar title="Overview" subtitle="Shadow AI threat detection gateway" />

      <section className="px-5 md:px-10 pt-14 pb-16 max-w-5xl">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <span className="inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/10 px-3 py-1 text-xs font-mono text-brand mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-brand animate-pulse-dot" />
            checkpoint active
          </span>
          <h1 className="font-display text-4xl md:text-5xl font-semibold leading-[1.1] max-w-2xl">
            Every prompt gets scanned before it reaches an external AI.
          </h1>
          <p className="text-muted mt-5 max-w-xl text-[15px] leading-relaxed">
            Employees paste source code, customer records, and credentials into public AI
            tools every day without meaning to. Sentinel sits in between, checks what's
            actually in the prompt, masks what shouldn't leave, and logs the rest.
          </p>
          <div className="flex flex-wrap gap-3 mt-8">
            <Link to="/gateway" className="inline-flex items-center gap-2 rounded-lg bg-brand text-onbrand font-semibold px-5 py-2.5 text-sm hover:brightness-110 transition">
              Open the Gateway <ArrowRight size={16} />
            </Link>
            <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-lg border border-line px-5 py-2.5 text-sm text-ink hover:bg-surface transition">
              View admin dashboard
            </Link>
          </div>
        </motion.div>
      </section>

      <section className="px-5 md:px-10 pb-14">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-5xl">
          <StatCard label="Prompts scanned" value={stats?.total_requests ?? '—'} accent="brand" />
          <StatCard label="Blocked" value={stats ? `${stats.block_rate}%` : '—'} accent="danger" sub="of total traffic" />
          <StatCard label="File scans" value={stats?.file_scans ?? '—'} accent="info" />
          <StatCard label="Active employees" value={stats ? Object.keys(stats.top_users || {}).length : '—'} accent="safe" />
        </div>
      </section>

      <section className="px-5 md:px-10 pb-20 max-w-5xl">
        <h2 className="font-display text-xl font-semibold mb-6">How it holds the line</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {PILLARS.map(({ icon: Icon, title, text }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: i * 0.06 }}
              className="rounded-xl border border-line bg-surface p-5"
            >
              <Icon size={20} className="text-brand mb-3" />
              <h3 className="font-display font-semibold text-sm mb-1.5">{title}</h3>
              <p className="text-muted text-sm leading-relaxed">{text}</p>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  )
}
