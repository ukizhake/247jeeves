import type { SimulationSummary } from '../types'

function usd(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

function pctTaxableSs(summary: SimulationSummary) {
  const gross = summary.first_year_social_security ?? 0
  const taxable = summary.first_year_taxable_ss ?? 0
  if (!gross) return '—'
  return `${Math.round((taxable / gross) * 100)}% of SS taxed`
}

export function SummaryCards({ summary }: { summary: SimulationSummary }) {
  const cards = [
    {
      label: 'Standard deductions (year 1)',
      value: usd(summary.first_year_total_deductions ?? 0),
      sub: 'Not Roth conversion — that is taxable income',
    },
    {
      label: 'Roth conversion (year 1)',
      value: usd(summary.first_year_roth_conversion ?? 0),
    },
    {
      label: 'Social Security (year 1)',
      value: pctTaxableSs(summary),
      sub: summary.first_year_social_security
        ? `${usd(summary.first_year_taxable_ss ?? 0)} taxable of ${usd(summary.first_year_social_security)}`
        : undefined,
    },
    { label: 'RMD at age 75', value: usd(summary.rmd_at_age_75) },
    { label: 'IRA balance at 75', value: usd(summary.ira_balance_at_age_75) },
    { label: 'Lifetime federal tax (est.)', value: usd(summary.lifetime_federal_tax) },
    { label: 'Lifetime NIIT (3.8%)', value: usd(summary.lifetime_niit ?? 0) },
    { label: 'Final total wealth', value: usd(summary.final_total_wealth) },
  ]

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {cards.map((c) => (
        <div
          key={c.label}
          className="rounded-xl border border-slate-800 bg-slate-900/80 px-4 py-3"
        >
          <p className="text-xs uppercase tracking-wide text-slate-500">{c.label}</p>
          <p className="mt-1 text-lg font-semibold text-white">{c.value}</p>
          {'sub' in c && c.sub && <p className="mt-1 text-xs text-slate-500">{c.sub}</p>}
        </div>
      ))}
    </div>
  )
}
