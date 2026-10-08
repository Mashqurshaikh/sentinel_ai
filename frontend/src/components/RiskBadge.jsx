const STYLES = {
  low: 'bg-safe/10 text-safe border-safe/30',
  medium: 'bg-warn/10 text-warn border-warn/30',
  high: 'bg-danger/10 text-danger border-danger/30',
}

const LABELS = { low: 'Low risk', medium: 'Medium risk', high: 'High risk' }

export default function RiskBadge({ level, size = 'md' }) {
  const cls = STYLES[level] || STYLES.low
  const pad = size === 'lg' ? 'px-4 py-1.5 text-sm' : 'px-3 py-1 text-xs'
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-semibold uppercase tracking-wide font-display ${cls} ${pad}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {LABELS[level] || level}
    </span>
  )
}
