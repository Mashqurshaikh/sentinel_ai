import { useEffect, useState } from 'react'
import { Sparkles } from 'lucide-react'
import { getProviders } from '../api/client'

const PROVIDER_META = {
  claude: { label: 'Claude', color: 'text-brand' },
  chatgpt: { label: 'ChatGPT', color: 'text-safe' },
  gemini: { label: 'Gemini', color: 'text-info' },
}

export default function ProviderSelector({ value, onChange }) {
  const [status, setStatus] = useState({ claude: false, chatgpt: false, gemini: false })

  useEffect(() => {
    getProviders().then(setStatus).catch(() => {})
  }, [])

  return (
    <div>
      <label className="text-xs text-muted font-mono block mb-1.5 flex items-center gap-1.5">
        <Sparkles size={12} /> send response through
      </label>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onChange(null)}
          className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition ${
            value === null ? 'border-brand text-brand bg-brand/10' : 'border-line text-muted hover:text-ink'
          }`}
        >
          Don't forward
        </button>
        {Object.entries(PROVIDER_META).map(([key, meta]) => {
          const available = status[key]
          return (
            <button
              type="button"
              key={key}
              disabled={!available}
              onClick={() => onChange(key)}
              title={available ? `Forward to ${meta.label}` : `${meta.label} needs an API key configured on the server`}
              className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition disabled:opacity-40 disabled:cursor-not-allowed ${
                value === key ? `border-brand ${meta.color} bg-brand/10` : 'border-line text-muted hover:text-ink'
              }`}
            >
              {meta.label}{!available && ' (no key)'}
            </button>
          )
        })}
      </div>
    </div>
  )
}
