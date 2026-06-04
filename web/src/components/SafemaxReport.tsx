import type { SafemaxReportResult } from '../types'

function usd(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

function pctRate(n: number) {
  return `${(n * 100).toFixed(2)}%`
}

const BAND_LABELS: Record<string, string> = {
  low: 'Low valuation (cheap stocks)',
  moderate: 'Moderate',
  elevated: 'Elevated',
  high: 'High valuation (expensive stocks)',
}

export function SafemaxReport({ result }: { result: SafemaxReportResult }) {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-indigo-800/50 bg-indigo-950/20 p-4 text-sm text-slate-300">
        <p className="font-medium text-indigo-300">SAFEMAX vs Shiller CAPE (educational)</p>
        <p className="mt-2">
          Deck methodology: 30-year COLA withdrawals, 55/40/5 allocation, tax-advantaged accounts.
          Your estimate uses CAPE{' '}
          <span className="tabular-nums text-slate-100">{result.shiller_cape.toFixed(1)}</span>
          {result.cape_source === 'default_assumption' && (
            <span className="text-slate-500"> (default — enter current CAPE in profile)</span>
          )}
          .
        </p>
        <p className="mt-2 text-xs text-slate-500">{result.horizon_adjustment_note}</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
          <p className="text-xs text-slate-500">CAPE-based SAFEMAX</p>
          <p className="mt-1 text-lg font-medium text-emerald-300 tabular-nums">
            {pctRate(result.estimated_safemax_pct)}
          </p>
          <p className="text-xs text-slate-500">{usd(result.estimated_safemax_dollars)} portfolio yr-1</p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
          <p className="text-xs text-slate-500">Universal 4.7% rule</p>
          <p className="mt-1 text-lg font-medium text-slate-200 tabular-nums">
            {pctRate(result.universal_rule_pct)}
          </p>
          <p className="text-xs text-slate-500">Worst-case across all historical retirees</p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
          <p className="text-xs text-slate-500">Your implied portfolio IWR</p>
          <p className="mt-1 text-lg font-medium text-amber-200 tabular-nums">
            {pctRate(result.current_implied_iwr_pct)}
          </p>
          <p className="text-xs text-slate-500">Spend {usd(result.current_annual_spending)}</p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
          <p className="text-xs text-slate-500">Valuation band</p>
          <p className="mt-1 text-sm font-medium text-slate-200">
            {BAND_LABELS[result.valuation_band] ?? result.valuation_band}
          </p>
          <p className="text-xs text-slate-500">Horizon {result.planning_horizon_years}y</p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <p className="border-b border-slate-800 bg-slate-900 px-3 py-2 text-sm font-medium text-slate-300">
          Historical deck anchors near your CAPE
        </p>
        <table className="w-full min-w-[520px] text-left text-sm">
          <thead className="bg-slate-900 text-slate-400">
            <tr>
              <th className="px-3 py-2">Retire date</th>
              <th className="px-3 py-2 text-right">CAPE</th>
              <th className="px-3 py-2 text-right">SAFEMAX</th>
              <th className="px-3 py-2">Note</th>
            </tr>
          </thead>
          <tbody>
            {result.nearby_anchors.map((a) => (
              <tr key={a.retirement_date} className="border-t border-slate-800">
                <td className="px-3 py-2 text-slate-300">{a.retirement_date || '—'}</td>
                <td className="px-3 py-2 text-right tabular-nums">{a.cape.toFixed(2)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{(a.safemax * 100).toFixed(2)}%</td>
                <td className="px-3 py-2 text-xs text-slate-500">{a.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {result.mc_paths > 0 && result.mc_success_at_current_spending != null && (
        <div className="rounded-xl border border-slate-800 p-4 text-sm">
          <p className="font-medium text-slate-300">
            Monte Carlo check ({result.mc_paths} paths, your return assumptions)
          </p>
          <ul className="mt-2 space-y-1 text-slate-400">
            <li>
              At current spending:{' '}
              <span className="text-slate-200 tabular-nums">
                {(result.mc_success_at_current_spending * 100).toFixed(1)}%
              </span>{' '}
              success · median end wealth{' '}
              {result.mc_median_wealth_at_current != null
                ? usd(result.mc_median_wealth_at_current)
                : '—'}
            </li>
            <li>
              At CAPE-estimated spending:{' '}
              <span className="text-slate-200 tabular-nums">
                {result.mc_success_at_estimated_safemax != null
                  ? `${(result.mc_success_at_estimated_safemax * 100).toFixed(1)}%`
                  : '—'}
              </span>{' '}
              success · median end wealth{' '}
              {result.mc_median_wealth_at_estimated != null
                ? usd(result.mc_median_wealth_at_estimated)
                : '—'}
            </li>
          </ul>
        </div>
      )}

      <ul className="list-disc space-y-2 pl-5 text-sm text-slate-400">
        {result.suggestions.map((s, i) => (
          <li key={i}>{s}</li>
        ))}
      </ul>
    </div>
  )
}
