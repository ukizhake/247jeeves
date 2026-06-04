import type { YearState } from '../types'

function money(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

function cell(n: number | undefined) {
  const v = n ?? 0
  return v > 0 ? money(v) : '—'
}

/** Portfolio income = fund + rental + SS + pension + consulting (no account withdrawals). */
function portfolioIncome(y: YearState): number {
  if (y.portfolio_income != null && y.portfolio_income > 0) return y.portfolio_income
  return (
    (y.fund_income ?? 0) +
    (y.rental_income ?? 0) +
    (y.social_security ?? 0) +
    (y.pension_income ?? 0) +
    (y.consulting_income ?? 0)
  )
}

const num = 'whitespace-nowrap px-2 py-1.5 text-right tabular-nums'
const lbl = 'whitespace-nowrap px-2 py-1.5 text-left'

export function SimulationTable({ years }: { years: YearState[] }) {
  const showSpouse = years.some((y) => y.spouse_age != null)
  const showSpouseSs = years.some((y) => (y.spouse_social_security ?? 0) > 0)
  const showWdBasis = years.some((y) => (y.withdrawal_taxable_basis ?? 0) > 0)
  const showNonBaseReturn = years.some(
    (y) => y.return_rate_applied != null && Math.abs(y.return_rate_applied - 0.06) > 0.001,
  )
  const showAnnuity = years.some((y) => (y.annuity_income ?? 0) > 0)
  const showIwr = years.some((y) => (y.implied_withdrawal_rate ?? 0) > 0.001)

  const portfolioCols =
    (showSpouseSs ? 7 : 6) + 3 + (showAnnuity ? 1 : 0) + (showIwr ? 1 : 0) + (showNonBaseReturn ? 1 : 0)
  const taxBreakdownCols = showWdBasis ? 9 : 7

  return (
    <div className="w-full overflow-x-auto rounded-xl border border-slate-800">
      <table className="w-max min-w-full text-left text-xs sm:text-sm">
        <thead className="bg-slate-900 text-slate-400">
          <tr className="border-b border-slate-700">
            <th colSpan={showSpouse ? 4 : 3} className="px-2 py-1.5" />
            <th
              colSpan={portfolioCols}
              className="px-2 py-1.5 text-center font-medium text-emerald-400/90"
            >
              Portfolio income & spending
            </th>
            <th colSpan={4} className="px-2 py-1.5 text-center font-medium text-sky-400/90">
              Balances
            </th>
            <th colSpan={5} className="px-2 py-1.5 text-center font-medium text-violet-400/90">
              Withdrawals
            </th>
            <th
              colSpan={taxBreakdownCols}
              className="px-2 py-1.5 text-center font-medium text-amber-400/90"
            >
              Tax income breakdown
            </th>
            <th colSpan={4} className="px-2 py-1.5 text-center font-medium text-orange-400/90">
              Tax owed
            </th>
            <th colSpan={2} className="px-2 py-1.5 text-center font-medium text-slate-500">
              Other
            </th>
          </tr>
          <tr>
            <th className={lbl}>Yr</th>
            <th className={num}>You</th>
            {showSpouse && <th className={num}>Sp</th>}
            <th className={lbl}>Phase</th>
            <th className={num}>Fund</th>
            <th className={num}>Rental</th>
            <th className={num}>Your SS</th>
            {showSpouseSs && <th className={num}>Sp SS</th>}
            <th className={num}>SS Σ</th>
            <th
              className={`${num} font-medium text-white`}
              title="Fund + rental + SS + pension + consulting"
            >
              Portfolio
            </th>
            <th className={num} title="Inflation-adjusted lifestyle spending target">
              Spend
            </th>
            {showAnnuity && (
              <th className={num} title="Guaranteed annuity / pension floor offsetting withdrawals">
                Annuity
              </th>
            )}
            <th
              className={num}
              title="Spending minus portfolio income, annuity, and RMD — amount pulled from accounts"
            >
              Wd need
            </th>
            {showIwr && (
              <th className={num} title="Portfolio withdrawal need ÷ wealth at start of year">
                IWR
              </th>
            )}
            {showNonBaseReturn && (
              <th className={num} title="Investment return applied this year (stress scenario)">
                Ret%
              </th>
            )}
            <th className={num}>Trad IRA</th>
            <th className={num}>Roth IRA</th>
            <th className={num}>Taxable</th>
            <th className={num}>Cash</th>
            <th className={num}>Trad w/d</th>
            <th className={num}>Tax w/d</th>
            <th className={num}>Roth w/d</th>
            <th className={num}>Roth conv</th>
            <th className={num}>RMD</th>
            {showWdBasis && (
              <th
                className={num}
                title="Return of cost basis from taxable brokerage sales — not taxed (default 80% of tax w/d)"
              >
                Wd basis
              </th>
            )}
            {showWdBasis && (
              <th className={num} title="Capital gain portion of taxable brokerage sales (default 20% of tax w/d)">
                Wd gain
              </th>
            )}
            <th className={num} title="Ordinary income stack: rental, non-Q divs, IRA w/d, Roth conv, taxable SS">
              Ordinary
            </th>
            <th className={num} title="LTCG stack: qualified divs + withdrawal gains">
              LTCG inc
            </th>
            <th className={num} title="Adjusted gross income">
              AGI
            </th>
            <th className={num}>Deduct</th>
            <th className={num} title="Taxable income after deductions (ordinary taxable + LTCG)">
              Tax inc
            </th>
            <th className={num}>Fed</th>
            <th className={num} title="Tax on long-term capital gains">
              LTCG tax
            </th>
            <th className={num}>NIIT</th>
            <th className={num}>SS tax</th>
            <th className={num}>Pension</th>
            <th className={num}>Consult</th>
          </tr>
        </thead>
        <tbody>
          {years.map((y) => (
            <tr key={y.year} className="border-t border-slate-800 hover:bg-slate-900/40">
              <td className={lbl}>{y.year}</td>
              <td className={num}>{y.age}</td>
              {showSpouse && <td className={num}>{y.spouse_age ?? '—'}</td>}
              <td className={`${lbl} capitalize`}>
                {y.phase.replace(/_/g, ' ').replace('early retirement', 'early')}
              </td>
              <td className={num}>{cell(y.fund_income)}</td>
              <td className={num}>{cell(y.rental_income)}</td>
              <td className={num}>{cell(y.primary_social_security ?? y.social_security)}</td>
              {showSpouseSs && <td className={num}>{cell(y.spouse_social_security)}</td>}
              <td className={num}>{cell(y.social_security)}</td>
              <td className={`${num} font-medium text-slate-200`}>{money(portfolioIncome(y))}</td>
              <td className={num}>{money(y.spending_target ?? 0)}</td>
              {showAnnuity && <td className={num}>{cell(y.annuity_income)}</td>}
              <td className={num}>{money(y.withdrawal_need ?? 0)}</td>
              {showIwr && (
                <td className={num}>
                  {y.implied_withdrawal_rate != null && y.implied_withdrawal_rate > 0
                    ? `${(y.implied_withdrawal_rate * 100).toFixed(1)}%`
                    : '—'}
                </td>
              )}
              {showNonBaseReturn && (
                <td className={num}>
                  {y.return_rate_applied != null
                    ? `${(y.return_rate_applied * 100).toFixed(1)}%`
                    : '—'}
                </td>
              )}
              <td className={num}>{money(y.traditional_ira)}</td>
              <td className={num}>{money(y.roth_ira)}</td>
              <td className={num}>{money(y.taxable)}</td>
              <td className={num}>{money(y.cash ?? 0)}</td>
              <td className={num}>{cell(y.withdrawal_ira)}</td>
              <td className={num}>{cell(y.withdrawal_taxable)}</td>
              <td className={num}>{cell(y.withdrawal_roth)}</td>
              <td className={num}>{cell(y.roth_conversion)}</td>
              <td className={num}>{y.rmd_required > 0 ? money(y.rmd_required) : '—'}</td>
              {showWdBasis && (
                <td className={`${num} text-slate-500`}>{cell(y.withdrawal_taxable_basis)}</td>
              )}
              {showWdBasis && <td className={num}>{cell(y.withdrawal_taxable_gain)}</td>}
              <td className={num}>{money(y.ordinary_income ?? 0)}</td>
              <td className={num}>{money(y.long_term_capital_gains ?? 0)}</td>
              <td className={`${num} font-medium text-slate-200`}>{money(y.agi ?? 0)}</td>
              <td className={num}>{money(y.total_deductions ?? 0)}</td>
              <td className={num}>{money(y.taxable_income ?? 0)}</td>
              <td className={num}>{money(y.federal_tax)}</td>
              <td className={num}>{cell(y.ltcg_tax)}</td>
              <td className={num}>{cell(y.niit_tax)}</td>
              <td className={num}>{cell(y.social_security_taxable)}</td>
              <td className={num}>{cell(y.pension_income)}</td>
              <td className={num}>{cell(y.consulting_income)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="px-3 py-2 text-xs text-slate-500">
        <strong className="text-slate-400">Portfolio</strong> = passive income (fund, rental, SS, etc.).{' '}
        <strong className="text-slate-400">Wd need</strong> = Spend − Portfolio − Annuity − RMD (net withdrawals
        from accounts). <strong className="text-slate-400">IWR</strong> = Wd need ÷ start-of-year wealth.{' '}
        <strong className="text-slate-400">Tax w/d</strong> / Trad w/d show where that need was funded.
      </p>
    </div>
  )
}
