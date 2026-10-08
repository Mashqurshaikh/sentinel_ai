import { useEffect, useState } from 'react'
import { Download, FileSpreadsheet } from 'lucide-react'
import TopBar from '../components/TopBar'
import { getAuditLogs, exportCsvUrl } from '../api/client'

export default function Reports() {
  const [logs, setLogs] = useState([])
  const [tagCounts, setTagCounts] = useState({})

  useEffect(() => {
    getAuditLogs(200).then(data => {
      setLogs(data)
      const counts = {}
      data.forEach(l => (l.compliance_tags || []).forEach(t => {
        if (!t) return
        counts[t] = (counts[t] || 0) + 1
      }))
      setTagCounts(counts)
    }).catch(() => {})
  }, [])

  const sortedTags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1])
  const maxCount = sortedTags[0]?.[1] || 1

  return (
    <div>
      <TopBar title="Reports" subtitle="Compliance exposure and exportable audit trail" />

      <div className="px-5 md:px-10 py-8 flex flex-col gap-8 max-w-5xl">
        <div className="rounded-xl border border-line bg-surface p-5 flex items-center justify-between flex-wrap gap-4">
          <div>
            <h3 className="font-display font-semibold text-sm mb-1">Full audit export</h3>
            <p className="text-xs text-muted">Every logged request, sanitized prompt, risk level, and department — as CSV.</p>
          </div>
          <a
            href={exportCsvUrl()}
            className="inline-flex items-center gap-2 rounded-lg bg-brand text-onbrand font-semibold px-4 py-2.5 text-sm hover:brightness-110 transition"
          >
            <Download size={15} /> Export CSV
          </a>
        </div>

        <div className="rounded-xl border border-line bg-surface p-5">
          <h3 className="font-display font-semibold text-sm mb-4">Regulatory exposure by tag</h3>
          {sortedTags.length === 0 && <p className="text-sm text-muted">No compliance-relevant matches logged yet.</p>}
          <div className="flex flex-col gap-3">
            {sortedTags.map(([tag, count]) => (
              <div key={tag} className="flex items-center gap-3">
                <span className="text-xs font-mono w-40 shrink-0 text-ink">{tag}</span>
                <div className="flex-1 h-2 rounded-full bg-surface-2 overflow-hidden">
                  <div className="h-full bg-info rounded-full" style={{ width: `${(count / maxCount) * 100}%` }} />
                </div>
                <span className="text-xs font-mono text-muted w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-line bg-surface overflow-hidden">
          <div className="px-5 py-4 border-b border-line flex items-center gap-2">
            <FileSpreadsheet size={16} className="text-brand" />
            <h3 className="font-display font-semibold text-sm">Recent audit entries</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted font-mono border-b border-line">
                  <th className="px-5 py-2 font-medium">time</th>
                  <th className="px-3 py-2 font-medium">user</th>
                  <th className="px-3 py-2 font-medium">dept</th>
                  <th className="px-3 py-2 font-medium">risk</th>
                  <th className="px-3 py-2 font-medium">action</th>
                  <th className="px-3 py-2 font-medium">source</th>
                </tr>
              </thead>
              <tbody>
                {logs.slice(0, 25).map(l => (
                  <tr key={l.id} className="border-b border-line/60 last:border-0">
                    <td className="px-5 py-2 text-xs font-mono text-muted whitespace-nowrap">{new Date(l.timestamp).toLocaleString()}</td>
                    <td className="px-3 py-2 text-xs font-mono">{l.user_id}</td>
                    <td className="px-3 py-2 text-xs text-muted">{l.department}</td>
                    <td className="px-3 py-2 text-xs uppercase font-mono">{l.risk_level}</td>
                    <td className="px-3 py-2 text-xs font-mono">{l.action}</td>
                    <td className="px-3 py-2 text-xs text-muted">{l.source}</td>
                  </tr>
                ))}
                {logs.length === 0 && (
                  <tr><td colSpan={6} className="px-5 py-8 text-center text-muted text-sm">No entries yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
