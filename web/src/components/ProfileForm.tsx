import type { Profile } from '../types'
import { FidelityImport } from './FidelityImport'

interface Props {
  profile: Profile
  onChange: (p: Profile) => void
  disabled?: boolean
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

export function ProfileForm({ profile, onChange, disabled }: Props) {
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
      <label className="block sm:col-span-2">
        <span className="text-sm text-slate-400">Plan name</span>
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
        <span className="text-sm text-slate-400">Plan through age</span>
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

      <p className="sm:col-span-2 text-sm font-medium text-slate-300">Annual income</p>
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

      <p className="sm:col-span-2 text-sm font-medium text-slate-300">Social Security</p>
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

      <FidelityImport profile={profile} onApply={onChange} disabled={disabled} />

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
    </div>
  )
}
