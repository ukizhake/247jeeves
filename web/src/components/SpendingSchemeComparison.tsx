import type { SpendingSchemeComparisonResult } from '../types'

function usd(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`
}

function bestScheme(
  schemes: SpendingSchemeComparisonResult['schemes'],
  key: 'success_rate' | 'median_final_wealth' | 'median_lifetime_spending',
): string | null {
  if (schemes.length === 0) return null
  let best = schemes[0]
  for (const s of schemes.slice(1)) {
    if (s[key] > best[key]) best = s
  }
  return best.scheme
}

export function SpendingSchemeComparison({ result }: { result: SpendingSchemeComparisonResult }) {
  const bestSuccess = bestScheme(result.schemes, 'success_rate')
  const bestWealth = bestScheme(result.schemes, 'median_final_wealth')
  const bestSpend = bestScheme(result.schemes, 'median_lifetime_spending')

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="bg-slate-900 text-slate-400">
          <tr>
            <th className="px-3 py-2">Spending scheme</th>
            <th className="px-3 py-2 text-right">Success rate</th>
            <th className="px-3 py-2 text-right">Median final wealth</th>
            <th className="px-3 py-2 text-right">10th–90th %ile wealth</th>
            <th className="px-3 py-2 text-right">Median lifetime spending</th>
            <th className="px-3 py-2 text-right">Median lifetime tax</th>
          </tr>
        </thead>
        <tbody>
          {result.schemes.map((s) => (
            <tr key={s.scheme} className="border-t border-slate-800 hover:bg-slate-900/40">
              <td className="px-3 py-2">
                <span className="font-medium text-slate-200">{s.label}</span>
                {s.scheme === bestSuccess && (
                  <span className="ml-2 rounded bg-emerald-900/60 px-1.5 py-0.5 text-xs text-emerald-400">
                    best success
                  </span>
                )}
                {s.scheme === bestWealth && s.scheme !== bestSuccess && (
                  <span className="ml-2 rounded bg-sky-900/60 px-1.5 py-0.5 text-xs text-sky-400">
                    highest wealth
                  </span>
                )}
                {s.scheme === bestSpend && s.scheme !== bestSuccess && s.scheme !== bestWealth && (
                  <span className="ml-2 rounded bg-violet-900/60 px-1.5 py-0.5 text-xs text-violet-400">
                    most spending
                  </span>
                )}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">{pct(s.success_rate)}</td>
              <td className="px-3 py-2 text-right tabular-nums">{usd(s.median_final_wealth)}</td>
              <td className="px-3 py-2 text-right tabular-nums">
                {usd(s.p10_final_wealth)} – {usd(s.p90_final_wealth)}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">{usd(s.median_lifetime_spending)}</td>
              <td className="px-3 py-2 text-right tabular-nums">{usd(s.median_lifetime_tax)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="px-3 py-2 text-xs text-slate-500">
        Same {result.num_paths.toLocaleString()} return paths for every scheme (COLA, fixed nominal,
        performance COLA, fixed % of portfolio). Success = no unfunded spending.
      </p>
    </div>
  )
}
