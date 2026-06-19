/**
 * LLM Settings page — shows all 6 providers with tier, signup links, and status.
 * To switch: edit backend/.env → LLM_PROVIDER=groq (or gemini/mistral/cohere) → restart backend.
 */

import { CheckCircle2, ExternalLink, Settings, XCircle, Zap } from 'lucide-react'
import { useEffect, useState } from 'react'
import axios from 'axios'

interface Provider {
  id: string
  name: string
  tier: 'FREE' | 'PAID'
  url: string
  env_key: string
  model: string
  configured: boolean
  active: boolean
}

interface ProvidersResponse {
  active_provider: string
  active_model: string
  switch_instructions: string
  providers: Provider[]
}

export function SettingsPage() {
  const [data, setData] = useState<ProvidersResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('http://localhost:8000/providers')
      .then(r => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="animate-fade-in space-y-8 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-indigo-400" />
          LLM Provider Settings
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          CareerGPT supports 6 AI providers. Start with any free one below — no billing needed.
        </p>
      </div>

      {/* Active provider banner */}
      {data && (
        <div className="p-4 bg-indigo-900/30 border border-indigo-700 rounded-xl flex items-center gap-3">
          <Zap className="w-5 h-5 text-indigo-400 flex-shrink-0" />
          <div>
            <p className="text-sm text-gray-300">
              Currently active: <span className="text-white font-bold uppercase">{data.active_provider}</span>
              <span className="text-gray-500 ml-2">→ {data.active_model}</span>
            </p>
            <p className="text-xs text-gray-500 mt-0.5">{data.switch_instructions}</p>
          </div>
        </div>
      )}

      {loading && <p className="text-gray-500 text-sm">Loading provider info...</p>}

      {/* Provider cards */}
      {data && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
            All Providers — recommended order (FREE first)
          </h2>

          {data.providers.map((p, idx) => (
            <div
              key={p.id}
              className={`border rounded-xl p-4 flex items-start justify-between gap-4 transition-all
                ${p.active ? 'border-indigo-600 bg-indigo-900/20' : 'border-gray-800 bg-gray-900 hover:border-gray-700'}`}
            >
              <div className="flex items-start gap-3 flex-1">
                {/* Number */}
                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0
                  ${p.active ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400'}`}>
                  {idx + 1}
                </span>

                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-gray-100">{p.name}</span>
                    {p.active && <span className="badge badge-blue">ACTIVE</span>}
                    <span className={p.tier === 'FREE' ? 'badge badge-green' : 'badge badge-yellow'}>
                      {p.tier}
                    </span>
                  </div>

                  <p className="text-xs text-gray-500 mt-1">Model: {p.model}</p>

                  {/* Config status */}
                  <div className="mt-1.5 text-xs">
                    {p.configured ? (
                      <span className="flex items-center gap-1 text-green-400">
                        <CheckCircle2 className="w-3 h-3" /> API key configured
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-gray-500">
                        <XCircle className="w-3 h-3" />
                        Set <code className="bg-gray-800 px-1 rounded text-indigo-400">{p.env_key}=...</code> in backend/.env
                      </span>
                    )}
                  </div>

                  {/* How to activate */}
                  {!p.active && (
                    <p className="text-xs text-gray-600 mt-1">
                      To use: set <code className="bg-gray-800 px-1 rounded">LLM_PROVIDER={p.id}</code> in backend/.env
                    </p>
                  )}
                </div>
              </div>

              {/* Get key button */}
              <a
                href={p.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300
                           border border-indigo-800 hover:border-indigo-600 rounded-lg px-3 py-1.5
                           transition-colors whitespace-nowrap flex-shrink-0"
              >
                Get Free Key <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          ))}
        </div>
      )}

      {/* Step-by-step guide */}
      <div className="card">
        <h2 className="section-title text-base">⚡ How to switch providers</h2>
        <ol className="space-y-3">
          {[
            { n: '1', t: 'Pick any FREE provider above (Groq is fastest)' },
            { n: '2', t: 'Click "Get Free Key" → sign up → copy your API key' },
            { n: '3', t: 'Open backend/.env → paste key (e.g. GROQ_API_KEY=gsk_...)' },
            { n: '4', t: 'Set LLM_PROVIDER=groq  (or gemini / mistral / cohere)' },
            { n: '5', t: 'Restart the backend — new key loads automatically' },
          ].map(s => (
            <li key={s.n} className="flex gap-3 text-sm text-gray-300">
              <span className="w-6 h-6 rounded-full bg-indigo-600/20 border border-indigo-600/40
                               flex items-center justify-center text-indigo-400 text-xs font-bold flex-shrink-0">
                {s.n}
              </span>
              {s.t}
            </li>
          ))}
        </ol>
      </div>

      {/* Quick reference table */}
      <div className="card overflow-hidden">
        <h2 className="section-title text-base">🔗 Quick Reference</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-left">
              <th className="text-gray-500 pb-2 font-medium">Provider</th>
              <th className="text-gray-500 pb-2 font-medium">Tier</th>
              <th className="text-gray-500 pb-2 font-medium">Signup URL</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {[
              { name: 'Groq',      tier: 'FREE', url: 'https://console.groq.com' },
              { name: 'Gemini',    tier: 'FREE', url: 'https://aistudio.google.com/apikey' },
              { name: 'Mistral',   tier: 'FREE', url: 'https://console.mistral.ai' },
              { name: 'Cohere',    tier: 'FREE', url: 'https://dashboard.cohere.com' },
              { name: 'Anthropic', tier: 'PAID', url: 'https://console.anthropic.com' },
              { name: 'OpenAI',    tier: 'PAID', url: 'https://platform.openai.com/api-keys' },
            ].map(r => (
              <tr key={r.name}>
                <td className="py-2 text-gray-200 font-medium">{r.name}</td>
                <td className="py-2">
                  <span className={r.tier === 'FREE' ? 'badge badge-green' : 'badge badge-yellow'}>{r.tier}</span>
                </td>
                <td className="py-2">
                  <a href={r.url} target="_blank" rel="noopener noreferrer"
                    className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                    {r.url.replace('https://', '')} <ExternalLink className="w-3 h-3" />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
