import { motion } from 'framer-motion'
import { Globe, MessageSquareText, KeyRound, Webhook, CheckCircle2, Clock } from 'lucide-react'
import TopBar from '../components/TopBar'

const INTEGRATIONS = [
  {
    icon: Globe,
    title: 'Browser extension',
    status: 'planned',
    text: 'Intercepts text typed directly into chatgpt.com, claude.ai, and gemini.google.com before it\u2019s submitted, calling the same /analyze endpoint this dashboard uses.',
  },
  {
    icon: MessageSquareText,
    title: 'Slack / Teams alerts',
    status: 'planned',
    text: 'The Threat Intelligence agent already generates alert objects — wiring them to a webhook is a one-function change in agents/threat_intel_agent.py.',
  },
  {
    icon: KeyRound,
    title: 'SSO / SCIM provisioning',
    status: 'planned',
    text: 'Swap the free-text employee ID field for real identity — department and role would come from the directory instead of manual entry.',
  },
  {
    icon: Webhook,
    title: 'SIEM export',
    status: 'available',
    text: 'The audit log already exports as CSV from the Reports tab; a scheduled push to Splunk/Elastic is a matter of pointing a cron job at /export/csv.',
  },
]

export default function Integrations() {
  return (
    <div>
      <TopBar title="Integrations" subtitle="Where this gateway plugs into the rest of the stack" />

      <div className="px-5 md:px-10 py-8 max-w-4xl">
        <p className="text-sm text-muted mb-8 max-w-xl leading-relaxed">
          The core detection engine is transport-agnostic — anything that can make an HTTP
          request can sit in front of it. These are the integration points that make the most
          sense for a real deployment, in rough priority order.
        </p>

        <div className="flex flex-col gap-4">
          {INTEGRATIONS.map(({ icon: Icon, title, status, text }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.06 }}
              className="rounded-xl border border-line bg-surface p-5 flex gap-4"
            >
              <div className="w-10 h-10 rounded-lg bg-surface-2 flex items-center justify-center shrink-0">
                <Icon size={18} className="text-brand" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-display font-semibold text-sm">{title}</h3>
                  {status === 'available' ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono uppercase text-safe bg-safe/10 px-2 py-0.5 rounded-full">
                      <CheckCircle2 size={11} /> available now
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono uppercase text-muted bg-surface-2 px-2 py-0.5 rounded-full">
                      <Clock size={11} /> planned
                    </span>
                  )}
                </div>
                <p className="text-sm text-muted leading-relaxed">{text}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
