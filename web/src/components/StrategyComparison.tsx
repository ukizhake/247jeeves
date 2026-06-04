import type { StrategyComparisonResult } from '../types'

function usd(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`
}

function bestPolicy(
  strategies: StrategyComparisonResult['strategies'],
  key: 'success_rate' | 'median_final_wealth',
): string | null {
  if (strategies.length === 0) return null
  let best = strategies[0]
  for (const s of strategies.slice(1)) {
    if (s[key] > best[key]) best = s
  }
  return best.policy
}

export function StrategyComparison({ result }: { result: StrategyComparisonResult }) {
  const bestSuccess = bestPolicy(result.strategies, 'success_rate')
  const bestWealth = bestPolicy(result.strategies, 'median_final_wealth')

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="bg-slate-900 text-slate-400">
          <tr>
            <th className="px-3 py-2">Withdrawal strategy</th>
            <th className="px-3 py-2 text-right">Success rate</th>
            <th className="px-3 py-2 text-right">Median final wealth</th>
            <th className="px-3 py-2 text-right">10th–90th %ile</th>
            <th className="px-3 py-2 text-right">Median lifetime tax</th>
          </tr>
        </thead>
        <tbody>
          {result.strategies.map((s) => (
            <tr key={s.policy} className="border-t border-slate-800 hover:bg-slate-900/40">
              <td className="px-3 py-2">
                <span className="font-medium text-slate-200">{s.label}</span>
                {s.policy === bestSuccess && (
                  <span className="ml-2 rounded bg-emerald-900/60 px-1.5 py-0.5 text-xs text-emerald-400">
                    best success
                  </span>
                )}
                {s.policy === bestWealth && s.policy !== bestSuccess && (
                  <span className="ml-2 rounded bg-sky-900/60 px-1.5 py-0.5 text-xs text-sky-400">
                    highest median
                  </span>
                )}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">{pct(s.success_rate)}</td>
              <td className="px-3 py-2 text-right tabular-nums">{usd(s.median_final_wealth)}</td>
              <td className="px-3 py-2 text-right tabular-nums">
                {usd(s.p10_final_wealth)} – {usd(s.p90_final_wealth)}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">{usd(s.median_lifetime_tax)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="px-3 py-2 text-xs text-slate-500">
        Same {result.num_paths.toLocaleString()} random return paths for every strategy. Success = no
        unfunded spending. Return: {pct(result.mean_return)} ± {pct(result.return_volatility)} vol.
      </p>
    </div>
  )
}
