import { publicText } from '../debug'
import type { RebalanceReportResult } from '../types'

function money(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`
}

interface Props {
  result: RebalanceReportResult
  debug?: boolean
}

export function RebalanceReport({ result, debug = false }: Props) {
  return (
    <div className="rounded-xl border border-sky-800/60 bg-sky-950/20 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium text-sky-400">Rebalance report · target 55/40/5</p>
        <span
          className={`rounded-full px-3 py-1 text-xs ${
            result.needs_rebalance
              ? 'bg-amber-950/60 text-amber-200'
              : 'bg-emerald-950/60 text-emerald-200'
          }`}
        >
          {result.needs_rebalance
            ? `Rebalance suggested (max drift ${pct(result.max_drift_pct)})`
            : 'Within band — hold'}
        </span>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="text-xs text-slate-500">Total wealth</p>
          <p className="text-lg font-semibold text-slate-200">{money(result.total_wealth)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Tax-advantaged (IRA + Roth)</p>
          <p className="text-lg font-semibold text-slate-200">
            {money(result.tax_advantaged_balance)}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Taxable brokerage</p>
          <p className="text-lg font-semibold text-slate-200">{money(result.taxable_balance)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Cash accounts</p>
          <p className="text-lg font-semibold text-slate-200">{money(result.cash_balance)}</p>
        </div>
      </div>

      <div className="mt-4 overflow-x-auto rounded-lg border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900 text-slate-400">
            <tr>
              <th className="px-3 py-2">Sleeve</th>
              <th className="px-3 py-2 text-right">Target</th>
              <th className="px-3 py-2 text-right">Current</th>
              <th className="px-3 py-2 text-right">Drift $</th>
            </tr>
          </thead>
          <tbody>
            {result.slices.map((s) => (
              <tr key={s.asset} className="border-t border-slate-800">
                <td className="px-3 py-2 capitalize">{s.asset}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {pct(s.target_pct)} · {money(s.target_dollars)}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {pct(s.current_pct)} · {money(s.current_dollars)}
                </td>
                <td
                  className={`px-3 py-2 text-right tabular-nums ${
                    s.drift_dollars > 0 ? 'text-amber-300' : s.drift_dollars < 0 ? 'text-emerald-300' : ''
                  }`}
                >
                  {s.drift_dollars > 0 ? '+' : ''}
                  {money(s.drift_dollars)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {result.trades.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-medium text-slate-300">Suggested trades</p>
          <ul className="mt-2 space-y-1 text-sm text-slate-400">
            {result.trades.map((t, i) => (
              <li key={`${t.asset}-${t.action}-${i}`}>
                <span className="capitalize text-slate-200">{t.action}</span> {money(t.amount)}{' '}
                <span className="capitalize">{t.asset}</span>
                {t.preferred_location === 'tax_advantaged' && (
                  <span className="text-sky-400"> · prefer IRA/Roth</span>
                )}
              </li>
            ))}
          </ul>
          {result.rebalance_in_tax_advantaged > 0 && (
            <p className="mt-2 text-xs text-slate-500">
              ~{money(result.rebalance_in_tax_advantaged)} of moves can be done in tax-advantaged
              accounts.
            </p>
          )}
        </div>
      )}

      {debug && result.rebalance_notes.length > 0 && (
        <ul className="mt-4 list-inside list-disc space-y-1 text-sm text-slate-400">
          {result.rebalance_notes.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      )}

      <ul className="mt-3 list-inside list-disc space-y-1 text-xs text-slate-500">
        {result.suggestions.map((s) => (
          <li key={s}>{publicText(s, debug)}</li>
        ))}
      </ul>
    </div>
  )
}
