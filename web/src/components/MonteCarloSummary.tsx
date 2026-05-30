import type { MonteCarloResult } from '../types'

function usd(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`
}

export function MonteCarloSummary({ result }: { result: MonteCarloResult }) {
  const successPct = result.success_rate * 100
  const successColor =
    successPct >= 90 ? 'text-emerald-400' : successPct >= 75 ? 'text-amber-400' : 'text-red-400'

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
        <p className="text-xs text-slate-500">Success rate</p>
        <p className={`mt-1 text-2xl font-semibold tabular-nums ${successColor}`}>
          {successPct.toFixed(1)}%
        </p>
        <p className="mt-1 text-xs text-slate-500">
          No unfunded spending in {result.num_paths.toLocaleString()} random paths
        </p>
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
        <p className="text-xs text-slate-500">Median final wealth</p>
        <p className="mt-1 text-2xl font-semibold tabular-nums">{usd(result.median_final_wealth)}</p>
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
        <p className="text-xs text-slate-500">10th–90th %ile (final)</p>
        <p className="mt-1 text-lg font-semibold tabular-nums">
          {usd(result.p10_final_wealth)} – {usd(result.p90_final_wealth)}
        </p>
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
        <p className="text-xs text-slate-500">Return assumption</p>
        <p className="mt-1 text-lg font-semibold tabular-nums">
          {pct(result.mean_return)} ± {pct(result.return_volatility)} vol
        </p>
      </div>
    </div>
  )
}
