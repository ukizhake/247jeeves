import type { AssetAllocation, Profile } from '../types'
import { FidelityImport } from './FidelityImport'
import { FormAccordion } from './FormAccordion'
import { FormSection } from './FormSection'

interface Props {
  profile: Profile
  onChange: (p: Profile) => void
  disabled?: boolean
  debug?: boolean
}

function num(v: string) {
  const n = parseFloat(v)
  return Number.isFinite(n) ? n : 0
}

const defaultIncome = {
  rental: 0,
  dividends: 0,
  pension: 0,
  consulting: 0,
  other_ordinary: 0,
}

const MAX_SS_MONTHLY = 6_500

const DEFAULT_TARGET_ALLOC: AssetAllocation = { stocks: 0.55, bonds: 0.4, cash: 0.05 }

function monthlyError(monthly: number, who: string): string | null {
  if (monthly <= 0) return null
  if (monthly > MAX_SS_MONTHLY) {
    return `${who}: $${monthly.toLocaleString()}/mo is too high. Enter the monthly amount from ssa.gov (typically $1,500–$5,500) and re-enter.`
  }
  return null
}

export function validateProfileSocialSecurity(profile: Profile): string | null {
  const yourMonthly = Math.round(profile.social_security_annual_at_claim / 12) || 0
  const yourErr = monthlyError(yourMonthly, 'Your Social Security')
  if (yourErr) return yourErr
  if (profile.filing_status === 'mfj') {
    const spouseMonthly =
      Math.round((profile.spouse_social_security_annual_at_claim ?? 0) / 12) || 0
    return monthlyError(spouseMonthly, 'Spouse Social Security')
  }
  return null
}

function money(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

export function ProfileForm({ profile, onChange, disabled, debug = false }: Props) {
  const isCouple = profile.filing_status === 'mfj'
  const yourMonthly = Math.round(profile.social_security_annual_at_claim / 12) || 0
  const spouseMonthly = Math.round((profile.spouse_social_security_annual_at_claim ?? 0) / 12) || 0
  const householdSs =
    profile.social_security_annual_at_claim + (profile.spouse_social_security_annual_at_claim ?? 0)

  const startYear = profile.projection_start_year ?? 2026
  const spouseClaimAge =
    profile.spouse_social_security_claim_age ?? profile.social_security_claim_age
  const yourSsStartYear = startYear + (profile.social_security_claim_age - profile.age)
  const spouseSsStartYear =
    profile.spouse_age != null ? startYear + (spouseClaimAge - profile.spouse_age) : null

  const set = (patch: Partial<Profile>) => onChange({ ...profile, ...patch })
  const setAcct = (patch: Partial<Profile['accounts']>) =>
    onChange({ ...profile, accounts: { ...profile.accounts, ...patch } })
  const setInc = (patch: Partial<NonNullable<Profile['income']>>) =>
    onChange({ ...profile, income: { ...(profile.income ?? defaultIncome), ...patch } })
  const income = profile.income ?? defaultIncome

  function setHousehold(couple: boolean) {
    if (couple) {
      onChange({
        ...profile,
        filing_status: 'mfj',
        spouse_age: profile.spouse_age ?? Math.max(18, profile.age - 2),
        spouse_social_security_claim_age:
          profile.spouse_social_security_claim_age ?? profile.social_security_claim_age,
      })
    } else {
      onChange({
        ...profile,
        filing_status: 'single',
        spouse_age: undefined,
        spouse_social_security_annual_at_claim: 0,
        spouse_social_security_claim_age: undefined,
      })
    }
  }

  function setYourMonthly(monthly: number) {
    set({ social_security_annual_at_claim: monthly * 12 })
  }

  function setSpouseMonthly(monthly: number) {
    set({ spouse_social_security_annual_at_claim: monthly * 12 })
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <FormSection title="Profile & household" accent="violet">
      <label className="block sm:col-span-2">
        <span className="text-sm text-slate-400">{debug ? 'Plan name' : 'Name'}</span>
        <input
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.name}
          disabled={disabled}
          onChange={(e) => set({ name: e.target.value })}
        />
      </label>

      <fieldset className="sm:col-span-2">
        <legend className="text-sm font-medium text-slate-300">Household</legend>
        <div className="mt-2 flex rounded-lg border border-slate-700 p-1">
          <button
            type="button"
            disabled={disabled}
            onClick={() => setHousehold(false)}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition ${
              !isCouple
                ? 'bg-emerald-600 text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Single
          </button>
          <button
            type="button"
            disabled={disabled}
            onClick={() => setHousehold(true)}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition ${
              isCouple
                ? 'bg-emerald-600 text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Couple (MFJ)
          </button>
        </div>
        <p className="mt-1 text-xs text-slate-500">
          {isCouple
            ? 'Married filing jointly — wider brackets, combined Social Security, spouse age affects senior deductions.'
            : 'Single filer — single brackets and standard deduction.'}
        </p>
      </fieldset>

      <label className="block">
        <span className="text-sm text-slate-400">{isCouple ? 'Your age' : 'Age'}</span>
        <input
          type="number"
          min={18}
          max={100}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.age}
          disabled={disabled}
          onChange={(e) => set({ age: num(e.target.value) })}
        />
      </label>

      {isCouple && (
        <label className="block">
          <span className="text-sm text-slate-400">Spouse age</span>
          <input
            type="number"
            min={18}
            max={100}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
            value={profile.spouse_age ?? ''}
            disabled={disabled}
            onChange={(e) => {
              const v = e.target.value.trim()
              set({ spouse_age: v === '' ? undefined : num(v) })
            }}
          />
        </label>
      )}

      <label className="block">
        <span className="text-sm text-slate-400">
          {debug ? 'Plan through age' : 'Project through age'}
        </span>
        <input
          type="number"
          min={profile.age}
          max={105}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.plan_to_age ?? 95}
          disabled={disabled}
          onChange={(e) => set({ plan_to_age: num(e.target.value) })}
        />
      </label>

      <label className="block">
        <span className="text-sm text-slate-400">Projection starts (calendar year)</span>
        <input
          type="number"
          min={2020}
          max={2100}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={startYear}
          disabled={disabled}
          onChange={(e) => set({ projection_start_year: num(e.target.value) })}
        />
      </label>
      </FormSection>

      <FormSection title="Annual income" accent="teal">
      <label className="block">
        <span className="text-sm text-slate-400">Rental income</span>
        <input
          type="number"
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={income.rental}
          disabled={disabled}
          onChange={(e) => setInc({ rental: num(e.target.value) })}
        />
      </label>
      <label className="block">
        <span className="text-sm text-slate-400">Fund dividends (taxable)</span>
        <input
          type="number"
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={income.dividends}
          disabled={disabled}
          onChange={(e) => setInc({ dividends: num(e.target.value) })}
        />
      </label>
      <label className="block">
        <span className="text-sm text-slate-400">Pension</span>
        <input
          type="number"
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={income.pension}
          disabled={disabled}
          onChange={(e) => setInc({ pension: num(e.target.value) })}
        />
      </label>
      <label className="block">
        <span className="text-sm text-slate-400">Consulting / earned</span>
        <input
          type="number"
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={income.consulting}
          disabled={disabled}
          onChange={(e) => setInc({ consulting: num(e.target.value) })}
        />
      </label>
      </FormSection>

      <FormSection title="Social Security" accent="indigo">
      <p className="sm:col-span-2 text-xs text-slate-500">
        Enter the <strong className="font-medium text-slate-400">monthly</strong> benefit from{' '}
        <a
          href="https://www.ssa.gov/myaccount/"
          target="_blank"
          rel="noreferrer"
          className="text-emerald-400 underline"
        >
          ssa.gov
        </a>{' '}
        at your claim age — not the annual amount.
      </p>
      <label className="block">
        <span className="text-sm text-slate-400">
          {isCouple ? 'Your claim age' : 'Claim age'}
        </span>
        <select
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.social_security_claim_age}
          disabled={disabled}
          onChange={(e) => set({ social_security_claim_age: num(e.target.value) })}
        >
          {[62, 63, 64, 65, 66, 67, 68, 69, 70].map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
        <p className="mt-1 text-xs text-slate-500">
          Your SS starts in {yourSsStartYear} (you turn {profile.social_security_claim_age})
        </p>
      </label>

      {isCouple && (
        <label className="block">
          <span className="text-sm text-slate-400">Spouse claim age</span>
          <select
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
            value={spouseClaimAge}
            disabled={disabled}
            onChange={(e) =>
              set({ spouse_social_security_claim_age: num(e.target.value) })
            }
          >
            {[62, 63, 64, 65, 66, 67, 68, 69, 70].map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
          {spouseSsStartYear != null && profile.spouse_age != null && (
            <p className="mt-1 text-xs text-slate-500">
              Spouse SS starts in {spouseSsStartYear} (spouse turns {spouseClaimAge})
            </p>
          )}
        </label>
      )}
      <div className="block">
        <span className="text-sm text-slate-400">
          {isCouple ? 'Your monthly benefit at claim age' : 'Monthly benefit at claim age'}
        </span>
        <input
          type="number"
          step={1}
          min={0}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={yourMonthly || ''}
          disabled={disabled}
          onChange={(e) => setYourMonthly(num(e.target.value))}
        />
        <p className="mt-1 text-xs text-slate-500">
          Annual: {money(profile.social_security_annual_at_claim)}
        </p>
        {monthlyError(yourMonthly, 'Your Social Security') && (
          <p className="mt-1 text-xs text-red-400">
            {monthlyError(yourMonthly, 'Your Social Security')}
          </p>
        )}
      </div>

      {isCouple && (
        <div className="block">
          <span className="text-sm text-slate-400">Spouse monthly benefit at claim age</span>
          <input
            type="number"
            step={1}
            min={0}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
            value={spouseMonthly || ''}
            disabled={disabled}
            onChange={(e) => setSpouseMonthly(num(e.target.value))}
          />
          <p className="mt-1 text-xs text-slate-500">
            Annual: {money(profile.spouse_social_security_annual_at_claim ?? 0)}
          </p>
          {monthlyError(spouseMonthly, 'Spouse Social Security') && (
            <p className="mt-1 text-xs text-red-400">
              {monthlyError(spouseMonthly, 'Spouse Social Security')}
            </p>
          )}
        </div>
      )}

      {(yourMonthly > 0 || spouseMonthly > 0) && (
        <p className="sm:col-span-2 text-xs text-slate-400">
          When both are claiming: {money(householdSs)}/yr household (
          {money(profile.social_security_annual_at_claim)}
          {isCouple && spouseMonthly > 0
            ? ` + ${money(profile.spouse_social_security_annual_at_claim ?? 0)}`
            : ''}
          ). Amounts may start in different years if claim ages differ.
        </p>
      )}

      <label className="block">
        <span className="text-sm text-slate-400">SS COLA after claiming (optional)</span>
        <input
          type="number"
          step={0.1}
          placeholder={`Default ${(profile.inflation_rate * 100).toFixed(0)}% (inflation)`}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={
            profile.social_security_cola_rate != null
              ? profile.social_security_cola_rate * 100
              : ''
          }
          disabled={disabled}
          onChange={(e) => {
            const v = e.target.value.trim()
            set({
              social_security_cola_rate: v === '' ? null : num(v) / 100,
            })
          }}
        />
      </label>

      <label className="block">
        <span className="text-sm text-slate-400">Annual spending</span>
        <input
          type="number"
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.annual_spending}
          disabled={disabled}
          onChange={(e) => set({ annual_spending: num(e.target.value) })}
        />
      </label>
      </FormSection>

      <FormAccordion
        title="Withdrawal & spending path"
        accent="emerald"
        debugSuffix="(Phase 3a)"
        debug={debug}
      >
      <label className="block">
        <span className="text-sm text-slate-400">Withdrawal scheme</span>
        <select
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.withdrawal_scheme ?? 'performance_cola'}
          disabled={disabled}
          onChange={(e) =>
            set({
              withdrawal_scheme: e.target.value as Profile['withdrawal_scheme'],
            })
          }
        >
          <option value="performance_cola">Performance COLA (hold after down year)</option>
          <option value="cola">COLA every year</option>
          <option value="fixed_annuity">
            {debug
              ? 'Book FA (nominal lifestyle — not insurance)'
              : 'Fixed amount (nominal — not insurance)'}
          </option>
          <option value="fixed_percentage">Fixed % of portfolio (FP)</option>
          <option value="floor_ceiling">Floor & ceiling (F&C)</option>
        </select>
      </label>

      {((profile.withdrawal_scheme ?? '') === 'fixed_percentage' ||
        profile.withdrawal_scheme === 'floor_ceiling') && (
        <label className="block">
          <span className="text-sm text-slate-400">Initial withdrawal rate (% of portfolio)</span>
          <input
            type="number"
            min={2}
            max={20}
            step={0.1}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
            value={((profile.initial_withdrawal_rate ?? 0.047) * 100).toFixed(1)}
            disabled={disabled}
            onChange={(e) => set({ initial_withdrawal_rate: num(e.target.value) / 100 })}
          />
        </label>
      )}

      {profile.withdrawal_scheme === 'floor_ceiling' && (
        <>
          <label className="block">
            <span className="text-sm text-slate-400">F&C max raise vs prior year (%)</span>
            <input
              type="number"
              min={0}
              max={50}
              step={1}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
              value={((profile.floor_ceiling_raise_pct ?? 0.1) * 100).toFixed(0)}
              disabled={disabled}
              onChange={(e) => set({ floor_ceiling_raise_pct: num(e.target.value) / 100 })}
            />
          </label>
          <label className="block">
            <span className="text-sm text-slate-400">F&C max cut vs prior year (%)</span>
            <input
              type="number"
              min={0}
              max={50}
              step={1}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
              value={((profile.floor_ceiling_cut_pct ?? 0.1) * 100).toFixed(0)}
              disabled={disabled}
              onChange={(e) => set({ floor_ceiling_cut_pct: num(e.target.value) / 100 })}
            />
          </label>
        </>
      )}

      {profile.withdrawal_scheme === 'fixed_percentage' && (
        <p className="sm:col-span-2 text-xs text-slate-500">
          FP: spending moves with portfolio each year
          {debug ? ' (deck ~4.7% on 55/40/5).' : '.'}
        </p>
      )}

      <label className="block">
        <span className="text-sm text-slate-400">Shiller CAPE (optional)</span>
        <input
          type="number"
          min={5}
          max={60}
          step={0.1}
          placeholder="e.g. 32"
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.shiller_cape ?? ''}
          disabled={disabled}
          onChange={(e) => {
            const v = e.target.value.trim()
            set({ shiller_cape: v === '' ? null : num(v) })
          }}
        />
      </label>

      <label className="block">
        <span className="text-sm text-slate-400">Inflation regime (CAPE estimate)</span>
        <select
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.inflation_regime ?? 'normal'}
          disabled={disabled}
          onChange={(e) =>
            set({ inflation_regime: e.target.value as 'normal' | 'high' })
          }
        >
          <option value="normal">Normal</option>
          <option value="high">High inflation</option>
        </select>
      </label>

      <label className="block">
        <span className="text-sm text-slate-400">Annual review month</span>
        <select
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.annual_review_month ?? 10}
          disabled={disabled}
          onChange={(e) => set({ annual_review_month: num(e.target.value) })}
        >
          {[
            'January',
            'February',
            'March',
            'April',
            'May',
            'June',
            'July',
            'August',
            'September',
            'October',
            'November',
            'December',
          ].map((name, i) => (
            <option key={name} value={i + 1}>
              {name}
            </option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className="text-sm text-slate-400">Spending COLA (% / yr, optional)</span>
        <input
          type="number"
          step={0.1}
          placeholder={`Default ${(profile.inflation_rate * 100).toFixed(0)}% (inflation)`}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={
            profile.spending_cola_rate != null ? profile.spending_cola_rate * 100 : ''
          }
          disabled={disabled}
          onChange={(e) => {
            const v = e.target.value.trim()
            set({ spending_cola_rate: v === '' ? null : num(v) / 100 })
          }}
        />
      </label>

      {(profile.withdrawal_scheme ?? 'performance_cola') === 'performance_cola' && (
        <>
          <label className="flex items-center gap-2 text-sm text-slate-300 sm:col-span-2">
            <input
              type="checkbox"
              checked={profile.performance_skip_cola_after_down_year ?? true}
              disabled={disabled}
              onChange={(e) =>
                set({ performance_skip_cola_after_down_year: e.target.checked })
              }
              className="rounded border-slate-600"
            />
            Skip COLA bump after a down portfolio year
          </label>
          <label className="block">
            <span className="text-sm text-slate-400">Max raise cap (% / yr, optional)</span>
            <input
              type="number"
              step={1}
              placeholder="No cap"
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
              value={
                profile.performance_max_raise_pct != null
                  ? profile.performance_max_raise_pct * 100
                  : ''
              }
              disabled={disabled}
              onChange={(e) => {
                const v = e.target.value.trim()
                set({ performance_max_raise_pct: v === '' ? null : num(v) / 100 })
              }}
            />
          </label>
          <label className="block">
            <span className="text-sm text-slate-400">Max cut cap (% / yr, optional)</span>
            <input
              type="number"
              step={1}
              placeholder="No cap"
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
              value={
                profile.performance_max_cut_pct != null
                  ? profile.performance_max_cut_pct * 100
                  : ''
              }
              disabled={disabled}
              onChange={(e) => {
                const v = e.target.value.trim()
                set({ performance_max_cut_pct: v === '' ? null : num(v) / 100 })
              }}
            />
          </label>
        </>
      )}
      </FormAccordion>

      <FormAccordion
        title="Insurance annuity / SPIA"
        accent="amber"
        debugSuffix="(Phase 3d)"
        debug={debug}
      >
      <label className="block">
        <span className="text-sm text-slate-400">Guaranteed income type</span>
        <select
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.annuity_product_type ?? 'none'}
          disabled={disabled}
          onChange={(e) =>
            set({ annuity_product_type: e.target.value as Profile['annuity_product_type'] })
          }
        >
          <option value="none">None modeled</option>
          <option value="pension">Pension / existing floor</option>
          <option value="spira">SPIA (insurance)</option>
          <option value="mixed">Pension + SPIA</option>
        </select>
      </label>

      <label className="block">
        <span className="text-sm text-slate-400">Guaranteed income ($ / yr)</span>
        <input
          type="number"
          min={0}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.annuity_income_annual ?? 0}
          disabled={disabled}
          onChange={(e) => set({ annuity_income_annual: num(e.target.value) })}
        />
        <p className="mt-1 text-xs text-slate-500">Offsets portfolio withdrawals (pension or SPIA payout).</p>
      </label>

      <label className="block">
        <span className="text-sm text-slate-400">Hypothetical SPIA premium ($)</span>
        <input
          type="number"
          min={0}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.spira_premium_paid ?? 0}
          disabled={disabled}
          onChange={(e) => set({ spira_premium_paid: num(e.target.value) })}
        />
        <p className="mt-1 text-xs text-slate-500">
          {debug
            ? 'For "Compare annuity vs book FA" — reduces investable balances in that analysis.'
            : 'For "Compare annuity vs fixed spending" — reduces investable balances in that analysis.'}
        </p>
      </label>

      <label className="block">
        <span className="text-sm text-slate-400">SPIA payout rate (% of premium / yr)</span>
        <input
          type="number"
          min={2}
          max={15}
          step={0.5}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={((profile.spira_payout_rate ?? 0.06) * 100).toFixed(1)}
          disabled={disabled}
          onChange={(e) => set({ spira_payout_rate: num(e.target.value) / 100 })}
        />
      </label>

      <label className="block">
        <span className="text-sm text-slate-400">Annuity COLA (% / yr, optional)</span>
        <input
          type="number"
          step={0.1}
          placeholder="Fixed nominal if blank"
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.annuity_cola_rate != null ? profile.annuity_cola_rate * 100 : ''}
          disabled={disabled}
          onChange={(e) => {
            const v = e.target.value.trim()
            set({ annuity_cola_rate: v === '' ? null : num(v) / 100 })
          }}
        />
      </label>
      </FormAccordion>

      <FormAccordion
        title="Target allocation & rebalance"
        accent="sky"
        debugSuffix="(Phase 3b)"
        debug={debug}
      >
      {(() => {
        const target = profile.target_allocation ?? DEFAULT_TARGET_ALLOC
        const targetSum = (target.stocks + target.bonds + target.cash) * 100
        const setTarget = (patch: Partial<AssetAllocation>) =>
          set({ target_allocation: { ...target, ...patch } })
        return (
          <>
            <label className="block">
              <span className="text-sm text-slate-400">Target stocks (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={1}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                value={Math.round(target.stocks * 100)}
                disabled={disabled}
                onChange={(e) => setTarget({ stocks: num(e.target.value) / 100 })}
              />
            </label>
            <label className="block">
              <span className="text-sm text-slate-400">Target bonds (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={1}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                value={Math.round(target.bonds * 100)}
                disabled={disabled}
                onChange={(e) => setTarget({ bonds: num(e.target.value) / 100 })}
              />
            </label>
            <label className="block">
              <span className="text-sm text-slate-400">Target cash / T-bills (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={1}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                value={Math.round(target.cash * 100)}
                disabled={disabled}
                onChange={(e) => setTarget({ cash: num(e.target.value) / 100 })}
              />
            </label>
            {Math.abs(targetSum - 100) > 0.5 && (
              <p className="sm:col-span-2 text-xs text-amber-400">
                Target allocation sums to {targetSum.toFixed(0)}% — adjust to 100% before saving.
              </p>
            )}
          </>
        )
      })()}

      <label className="block">
        <span className="text-sm text-slate-400">Rebalance drift band (%)</span>
        <input
          type="number"
          min={0}
          max={10}
          step={0.5}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={((profile.rebalance_band_pct ?? 0.02) * 100).toFixed(1)}
          disabled={disabled}
          onChange={(e) => set({ rebalance_band_pct: num(e.target.value) / 100 })}
        />
        <p className="mt-1 text-xs text-slate-500">No trades if every sleeve is within this band (default 2%).</p>
      </label>

      <label className="flex items-center gap-2 text-sm text-slate-300 sm:col-span-2">
        <input
          type="checkbox"
          checked={profile.current_allocation != null}
          disabled={disabled}
          onChange={(e) => {
            if (e.target.checked) {
              set({
                current_allocation: profile.current_allocation ?? {
                  ...DEFAULT_TARGET_ALLOC,
                  stocks: 0.6,
                  bonds: 0.35,
                },
              })
            } else {
              set({ current_allocation: null })
            }
          }}
          className="rounded border-slate-600"
        />
        I know my current stocks/bonds/cash mix (not inferred from accounts)
      </label>

      {profile.current_allocation != null &&
        (() => {
          const cur = profile.current_allocation
          const curSum = (cur.stocks + cur.bonds + cur.cash) * 100
          const setCur = (patch: Partial<AssetAllocation>) =>
            set({ current_allocation: { ...cur, ...patch } })
          return (
            <>
              <label className="block">
                <span className="text-sm text-slate-400">Current stocks (%)</span>
                <input
                  type="number"
                  min={0}
                  max={100}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                  value={Math.round(cur.stocks * 100)}
                  disabled={disabled}
                  onChange={(e) => setCur({ stocks: num(e.target.value) / 100 })}
                />
              </label>
              <label className="block">
                <span className="text-sm text-slate-400">Current bonds (%)</span>
                <input
                  type="number"
                  min={0}
                  max={100}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                  value={Math.round(cur.bonds * 100)}
                  disabled={disabled}
                  onChange={(e) => setCur({ bonds: num(e.target.value) / 100 })}
                />
              </label>
              <label className="block">
                <span className="text-sm text-slate-400">Current cash (%)</span>
                <input
                  type="number"
                  min={0}
                  max={100}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                  value={Math.round(cur.cash * 100)}
                  disabled={disabled}
                  onChange={(e) => setCur({ cash: num(e.target.value) / 100 })}
                />
              </label>
              {Math.abs(curSum - 100) > 0.5 && (
                <p className="sm:col-span-2 text-xs text-amber-400">
                  Current allocation sums to {curSum.toFixed(0)}% — adjust to 100%.
                </p>
              )}
            </>
          )
        })()}
      </FormAccordion>

      <FormSection title="Market assumptions" accent="orange">
      <label className="block">
        <span className="text-sm text-slate-400">Expected return (% / yr)</span>
        <input
          type="number"
          min={0}
          max={20}
          step={0.5}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={(profile.return_rate * 100).toFixed(1)}
          disabled={disabled}
          onChange={(e) => set({ return_rate: num(e.target.value) / 100 })}
        />
        <p className="mt-1 text-xs text-slate-500">Applied to IRA, Roth, and taxable (cash uses 20% of this).</p>
      </label>

      <label className="block">
        <span className="text-sm text-slate-400">Return volatility (% / yr, Monte Carlo)</span>
        <input
          type="number"
          min={0}
          max={50}
          step={1}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={((profile.return_volatility ?? 0.15) * 100).toFixed(0)}
          disabled={disabled}
          onChange={(e) => set({ return_volatility: num(e.target.value) / 100 })}
        />
        <p className="mt-1 text-xs text-slate-500">Std dev around expected return (default 15%).</p>
      </label>

      <label className="block">
        <span className="text-sm text-slate-400">Inflation (% / yr)</span>
        <input
          type="number"
          min={0}
          max={10}
          step={0.5}
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={(profile.inflation_rate * 100).toFixed(1)}
          disabled={disabled}
          onChange={(e) => set({ inflation_rate: num(e.target.value) / 100 })}
        />
      </label>
      </FormSection>

      <FormSection title="Import balances" accent="cyan">
        <FidelityImport profile={profile} onApply={onChange} disabled={disabled} debug={debug} />
      </FormSection>

      <FormSection title="Account balances" accent="fuchsia">
      <label className="block">
        <span className="text-sm text-slate-400">Traditional IRA</span>
        <input
          type="number"
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.accounts.traditional_ira}
          disabled={disabled}
          onChange={(e) => setAcct({ traditional_ira: num(e.target.value) })}
        />
      </label>
      <label className="block">
        <span className="text-sm text-slate-400">Roth IRA</span>
        <input
          type="number"
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.accounts.roth_ira}
          disabled={disabled}
          onChange={(e) => setAcct({ roth_ira: num(e.target.value) })}
        />
      </label>
      <label className="block">
        <span className="text-sm text-slate-400">Taxable brokerage</span>
        <input
          type="number"
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.accounts.taxable}
          disabled={disabled}
          onChange={(e) => setAcct({ taxable: num(e.target.value) })}
        />
      </label>
      <label className="block">
        <span className="text-sm text-slate-400">Cash</span>
        <input
          type="number"
          className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          value={profile.accounts.cash}
          disabled={disabled}
          onChange={(e) => setAcct({ cash: num(e.target.value) })}
        />
      </label>
      </FormSection>
    </div>
  )
}
