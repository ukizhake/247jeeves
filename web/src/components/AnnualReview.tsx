import type { AnnualReviewResult } from '../types'

function money(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`
}

interface Props {
  result: AnnualReviewResult
  onApplyRecommended: () => void
  disabled?: boolean
}

export function AnnualReview({ result, onApplyRecommended, disabled }: Props) {
  const changeUp = result.cola_dollar_change > 0
  const changeDown = result.cola_dollar_change < 0

  return (
    <div className="rounded-xl border border-emerald-800/60 bg-emerald-950/20 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-emerald-400">
            Annual review · {result.review_month_name}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Scheme: {result.withdrawal_scheme.replace(/_/g, ' ')}
            {result.prior_year_return != null && (
              <> · Last year return: {pct(result.prior_year_return)}</>
            )}
          </p>
        </div>
        <button
          type="button"
          disabled={disabled}
          onClick={onApplyRecommended}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          Apply recommended spending
        </button>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="text-xs text-slate-500">Current spending</p>
          <p className="text-lg font-semibold text-slate-200">{money(result.current_annual_spending)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Recommended next year</p>
          <p
            className={`text-lg font-semibold ${
              changeUp ? 'text-emerald-300' : changeDown ? 'text-amber-300' : 'text-slate-200'
            }`}
          >
            {money(result.recommended_annual_spending)}
            {result.cola_dollar_change !== 0 && (
              <span className="ml-2 text-sm font-normal text-slate-400">
                ({changeUp ? '+' : ''}
                {money(result.cola_dollar_change)})
              </span>
            )}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Annuity / floor income</p>
          <p className="text-lg font-semibold text-slate-200">{money(result.annuity_income)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Implied portfolio IWR</p>
          <p className="text-lg font-semibold text-slate-200">{pct(result.implied_withdrawal_rate)}</p>
        </div>
      </div>

      <p className="mt-3 text-sm text-slate-300">{result.performance_note}</p>
      <p className="mt-1 text-xs text-slate-500">
        COLA rate {pct(result.cola_rate_applied)} · Portfolio income est.{' '}
        {money(result.portfolio_income_estimate)} · Est. portfolio withdrawal{' '}
        {money(result.portfolio_withdrawal_estimate)} · Wealth {money(result.total_wealth)}
      </p>

      {result.suggestions.length > 0 && (
        <ul className="mt-4 list-inside list-disc space-y-1 text-sm text-slate-400">
          {result.suggestions.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
