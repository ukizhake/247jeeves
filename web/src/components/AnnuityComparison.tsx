import type { AnnuityComparisonResult } from '../types'

function usd(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

function pct(n: number) {
  return `${n.toFixed(1)}%`
}

export function AnnuityComparison({
  result,
  debug = false,
}: {
  result: AnnuityComparisonResult
  debug?: boolean
}) {
  const edu = result.education

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-amber-800/50 bg-amber-950/20 p-4 text-sm text-slate-300">
        <p className="font-medium text-amber-300">Book FA vs insurance SPIA</p>
        <p className="mt-2">{edu.book_fa_explanation}</p>
        <p className="mt-2">{edu.spira_explanation}</p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="bg-slate-900 text-slate-400">
            <tr>
              <th className="px-3 py-2">Year-one snapshot</th>
              <th className="px-3 py-2 text-right">Wealth</th>
              <th className="px-3 py-2 text-right">Spend target</th>
              <th className="px-3 py-2 text-right">Annuity</th>
              <th className="px-3 py-2 text-right">Port. wd est.</th>
              <th className="px-3 py-2 text-right">Annuity % of spend</th>
            </tr>
          </thead>
          <tbody>
            {edu.year_one_snapshots.map((s) => (
              <tr key={s.variant} className="border-t border-slate-800">
                <td className="px-3 py-2">
                  <span className="font-medium text-slate-200">{s.label}</span>
                  {debug && s.notes && (
                    <p className="mt-0.5 text-xs text-slate-500">{s.notes}</p>
                  )}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">{usd(s.total_wealth)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{usd(s.annual_spending_target)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{usd(s.annuity_income)}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {usd(s.portfolio_withdrawal_estimate)}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">{pct(s.income_coverage_pct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {result.variants.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <p className="border-b border-slate-800 bg-slate-900 px-3 py-2 text-sm font-medium text-slate-300">
            Monte Carlo ({result.num_paths} shared paths)
          </p>
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-slate-900 text-slate-400">
              <tr>
                <th className="px-3 py-2">Variant</th>
                <th className="px-3 py-2 text-right">Success</th>
                <th className="px-3 py-2 text-right">Median wealth</th>
                <th className="px-3 py-2 text-right">Median lifetime spend</th>
                <th className="px-3 py-2 text-right">Median port. withdrawals</th>
              </tr>
            </thead>
            <tbody>
              {result.variants.map((v) => (
                <tr key={v.variant} className="border-t border-slate-800">
                  <td className="px-3 py-2 font-medium text-slate-200">{v.label}</td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {(v.success_rate * 100).toFixed(1)}%
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">{usd(v.median_final_wealth)}</td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {usd(v.median_lifetime_spending)}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {usd(v.median_portfolio_withdrawals)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {edu.suggestions.length > 0 && (
        <ul className="list-inside list-disc space-y-1 text-xs text-slate-500">
          {edu.suggestions.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
