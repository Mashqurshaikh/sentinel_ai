import { motion } from 'framer-motion'

export default function StatCard({ label, value, accent = 'brand', icon: Icon, sub }) {
  const accentClass = {
    brand: 'text-brand',
    safe: 'text-safe',
    danger: 'text-danger',
    info: 'text-info',
  }[accent]

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="rounded-xl border border-line bg-surface p-5 flex flex-col gap-2"
    >
      <div className="flex items-center justify-between">
        <span className="text-muted text-xs uppercase tracking-wider font-medium">{label}</span>
        {Icon && <Icon size={16} className={accentClass} />}
      </div>
      <span className={`font-display text-3xl font-semibold ${accentClass}`}>{value}</span>
      {sub && <span className="text-muted text-xs">{sub}</span>}
    </motion.div>
  )
}
