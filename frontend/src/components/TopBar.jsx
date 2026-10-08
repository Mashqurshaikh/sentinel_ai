export default function TopBar({ title, subtitle, live }) {
  return (
    <header className="flex items-center justify-between px-5 md:px-8 h-16 border-b border-line bg-bg/80 backdrop-blur sticky top-0 z-30">
      <div>
        <h1 className="font-display text-lg font-semibold text-ink leading-none">{title}</h1>
        {subtitle && <p className="text-xs text-muted mt-1">{subtitle}</p>}
      </div>
      {live !== undefined && (
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className={`w-2 h-2 rounded-full ${live ? 'bg-safe animate-pulse-dot' : 'bg-line'}`} />
          <span className={live ? 'text-safe' : 'text-muted'}>
            {live ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
      )}
    </header>
  )
}
