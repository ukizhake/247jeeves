import type { SimulationResult } from '../types'

function usd(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

const SCENARIO_NAMES: Record<string, string> = {
  base: 'Base',
  bad_early: 'Bad early',
  flat_low: 'Flat / low',
}

export function StressComparison({
  results,
  debug = false,
}: {
  results: SimulationResult[]
  debug?: boolean
}) {
  if (results.length === 0) return null

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-900 text-slate-400">
          <tr>
            <th className="px-3 py-2">Market scenario</th>
            <th className="px-3 py-2 text-right">Final wealth</th>
            <th className="px-3 py-2 text-right">Trad IRA at end</th>
            <th className="px-3 py-2 text-right">Lifetime tax</th>
            <th className="px-3 py-2 text-right">Yr 1 wd need</th>
            <th className="px-3 py-2 text-right">Yr 1 return</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => {
            const key = String(r.meta?.return_scenario ?? 'base')
            const y0 = r.years[0]
            const retPct = y0?.return_rate_applied != null ? `${(y0.return_rate_applied * 100).toFixed(1)}%` : '—'
            return (
              <tr key={key} className="border-t border-slate-800">
                <td className="px-3 py-2 font-medium">{SCENARIO_NAMES[key] ?? key}</td>
                <td className="px-3 py-2 text-right tabular-nums">{usd(r.summary.final_total_wealth)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{usd(r.summary.final_traditional_ira ?? 0)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{usd(r.summary.lifetime_federal_tax)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{usd(y0?.withdrawal_need ?? 0)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{retPct}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <p className="px-3 py-2 text-xs text-slate-500">
        Same {debug ? 'plan' : 'profile'}, different deterministic return paths. Withdrawal need = spending minus portfolio
        income (when net income is on).
      </p>
    </div>
  )
}
