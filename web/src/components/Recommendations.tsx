import type { Recommendation } from '../types'

function formatUsd(n: number | undefined) {
  if (n == null) return ''
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

export function Recommendations({ items }: { items: Recommendation[] }) {
  if (!items.length) {
    return <p className="text-slate-400">No recommendations for this scenario yet.</p>
  }

  return (
    <ul className="space-y-4">
      {items.map((rec) => (
        <li
          key={rec.rule_id}
          className="rounded-xl border border-emerald-900/50 bg-emerald-950/30 p-4"
        >
          <h3 className="font-semibold text-emerald-300">{rec.title}</h3>
          <p className="mt-1 text-sm text-slate-300">{rec.rationale}</p>
          <ul className="mt-3 space-y-2">
            {rec.actions.map((a, i) => (
              <li key={i} className="text-sm">
                {a.type === 'roth_convert' && (
                  <span>
                    Convert <strong>{formatUsd(a.amount)}</strong> to Roth — {a.note}
                  </span>
                )}
                {a.type === 'withdraw' && (
                  <span>
                    Withdraw <strong>{formatUsd(a.amount)}</strong> from {a.account} — {a.note}
                  </span>
                )}
                {a.type === 'delay_social_security' && <span>{a.note}</span>}
                {a.type === 'warn' && <span className="text-amber-300">⚠ {a.note}</span>}
                {a.type === 'info' && <span>{a.note}</span>}
                {a.type === 'asset_location' && (
                  <span className="text-sky-300">📍 {a.note}</span>
                )}
                {a.type === 'qcd' && <span className="text-violet-300">❤ {a.note}</span>}
              </li>
            ))}
          </ul>
          {rec.tradeoffs.length > 0 && (
            <p className="mt-2 text-xs text-slate-500">
              Tradeoffs: {rec.tradeoffs.join(' · ')}
            </p>
          )}
        </li>
      ))}
    </ul>
  )
}
