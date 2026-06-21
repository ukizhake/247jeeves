import { useEffect, useRef, useState } from 'react'
import {
  annualReview,
  annuityCompare,
  safemaxReport,
  rebalanceReport,
  monteCarlo,
  simulate,
  spendingCompare,
  strategyCompare,
} from './api/client'
import { AnnuityComparison } from './components/AnnuityComparison'
import { SafemaxReport } from './components/SafemaxReport'
import { AnnualReview } from './components/AnnualReview'
import { RebalanceReport } from './components/RebalanceReport'
import { BalanceChart } from './components/BalanceChart'
import { MonteCarloChart } from './components/MonteCarloChart'
import { MonteCarloSummary } from './components/MonteCarloSummary'
import { ProfileForm, validateProfileSocialSecurity } from './components/ProfileForm'
import { Recommendations } from './components/Recommendations'
import { SimulationTable } from './components/SimulationTable'
import { StressComparison } from './components/StressComparison'
import { SpendingSchemeComparison } from './components/SpendingSchemeComparison'
import { StrategyComparison } from './components/StrategyComparison'
import { SummaryCards } from './components/SummaryCards'
import { RETURN_SCENARIOS, type ReturnScenarioId } from './constants/returnScenarios'
import { spendingSchemeLabel, spendingSchemeOptions } from './constants/spendingSchemes'
import { defaultProfile, defaultSingleProfile } from './defaultProfile'
import { isDebugMode } from './debug'
import type {
  AnnuityComparisonResult,
  SafemaxReportResult,
  AnnualReviewResult,
  MonteCarloResult,
  RebalanceReportResult,
  Profile,
  ScenarioOverrides,
  SimulationResult,
  SpendingSchemeComparisonResult,
  StrategyComparisonResult,
  WithdrawalScheme,
} from './types'

function scenarioLabel(id: ReturnScenarioId): string {
  return RETURN_SCENARIOS.find((s) => s.id === id)?.label ?? id
}

function App() {
  const [profile, setProfile] = useState<Profile>(defaultProfile)
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [stressResults, setStressResults] = useState<SimulationResult[] | null>(null)
  const [monteCarloResult, setMonteCarloResult] = useState<MonteCarloResult | null>(null)
  const [strategyCompareResult, setStrategyCompareResult] = useState<StrategyComparisonResult | null>(null)
  const [annualReviewResult, setAnnualReviewResult] = useState<AnnualReviewResult | null>(null)
  const [rebalanceResult, setRebalanceResult] = useState<RebalanceReportResult | null>(null)
  const [spendingCompareResult, setSpendingCompareResult] =
    useState<SpendingSchemeComparisonResult | null>(null)
  const [annuityCompareResult, setAnnuityCompareResult] =
    useState<AnnuityComparisonResult | null>(null)
  const [safemaxResult, setSafemaxResult] = useState<SafemaxReportResult | null>(null)
  const [priorYearReturn, setPriorYearReturn] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [rothOverride, setRothOverride] = useState<string>('')
  const [returnScenario, setReturnScenario] = useState<ReturnScenarioId>('base')
  const [netPortfolioIncome, setNetPortfolioIncome] = useState(true)
  const [spendingScenarioOverride, setSpendingScenarioOverride] = useState<WithdrawalScheme | ''>('')
  const agesInitialized = useRef(false)

  function clearAllResults() {
    setResult(null)
    setStressResults(null)
    setMonteCarloResult(null)
    setStrategyCompareResult(null)
    setAnnualReviewResult(null)
    setRebalanceResult(null)
    setSpendingCompareResult(null)
    setAnnuityCompareResult(null)
    setSafemaxResult(null)
  }

  // Stale projection: table keeps last run's ages until you re-run. Clear when ages change.
  useEffect(() => {
    if (!agesInitialized.current) {
      agesInitialized.current = true
      return
    }
    clearAllResults()
  }, [profile.age, profile.spouse_age])

  function buildScenarioOverrides(name: string, scenarioId: ReturnScenarioId): ScenarioOverrides {
    const rothTrimmed = rothOverride.trim()
    let rothConversion: number | null = null
    if (rothTrimmed !== '') {
      const parsed = parseFloat(rothTrimmed)
      if (!Number.isFinite(parsed) || parsed < 0) {
        throw new Error('Roth conversion override must be a non-negative number (e.g. 20000).')
      }
      rothConversion = parsed
    }
    return {
      name,
      roth_conversion_annual: rothConversion,
      target_bracket_rate: 0.22,
      return_scenario: scenarioId,
      net_portfolio_income: netPortfolioIncome,
      spending_scheme_override: spendingScenarioOverride === '' ? null : spendingScenarioOverride,
    }
  }

  async function runSimulate() {
    setLoading(true)
    setError(null)
    setStressResults(null)
    setMonteCarloResult(null)
    setStrategyCompareResult(null)
    setAnnualReviewResult(null)
    setRebalanceResult(null)
    setSpendingCompareResult(null)
    setAnnuityCompareResult(null)
    setSafemaxResult(null)
    const ssError = validateProfileSocialSecurity(profile)
    if (ssError) {
      setError(ssError)
      setLoading(false)
      return
    }
    try {
      const sim = await simulate(
        profile,
        buildScenarioOverrides(
          rothOverride.trim() === '' ? `Base (${scenarioLabel(returnScenario)})` : `Roth override`,
          returnScenario,
        ),
      )
      setResult(sim)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Simulation failed')
    } finally {
      setLoading(false)
    }
  }

  async function compareStressScenarios() {
    setLoading(true)
    setError(null)
    setResult(null)
    setMonteCarloResult(null)
    setStrategyCompareResult(null)
    setAnnualReviewResult(null)
    setRebalanceResult(null)
    setSpendingCompareResult(null)
    setAnnuityCompareResult(null)
    setSafemaxResult(null)
    const ssError = validateProfileSocialSecurity(profile)
    if (ssError) {
      setError(ssError)
      setLoading(false)
      return
    }
    try {
      const results: SimulationResult[] = []
      for (const scenario of RETURN_SCENARIOS) {
        const sim = await simulate(
          profile,
          buildScenarioOverrides(`Compare: ${scenario.id}`, scenario.id),
        )
        results.push(sim)
      }
      setStressResults(results)
      setResult(results[0])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Comparison failed')
    } finally {
      setLoading(false)
    }
  }

  async function runMonteCarlo() {
    setLoading(true)
    setError(null)
    setStressResults(null)
    setStrategyCompareResult(null)
    setAnnualReviewResult(null)
    setRebalanceResult(null)
    setSpendingCompareResult(null)
    setAnnuityCompareResult(null)
    setSafemaxResult(null)
    setResult(null)
    const ssError = validateProfileSocialSecurity(profile)
    if (ssError) {
      setError(ssError)
      setLoading(false)
      return
    }
    try {
      const scenario = buildScenarioOverrides('Monte Carlo', 'base')
      const mc = await monteCarlo(profile, { scenario, num_paths: 500 })
      setMonteCarloResult(mc)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Monte Carlo failed')
    } finally {
      setLoading(false)
    }
  }

  function parsePriorYearReturn(): number | null {
    const trimmed = priorYearReturn.trim()
    if (trimmed === '') return null
    const parsed = parseFloat(trimmed)
    if (!Number.isFinite(parsed)) {
      throw new Error('Prior year return must be a number (e.g. 8 for +8%, or -12 for -12%).')
    }
    return parsed > 1 || parsed < -1 ? parsed / 100 : parsed
  }

  async function runRebalanceReport() {
    setLoading(true)
    setError(null)
    setStressResults(null)
    setMonteCarloResult(null)
    setStrategyCompareResult(null)
    setAnnualReviewResult(null)
    setRebalanceResult(null)
    setSpendingCompareResult(null)
    setAnnuityCompareResult(null)
    setSafemaxResult(null)
    setResult(null)
    const ssError = validateProfileSocialSecurity(profile)
    if (ssError) {
      setError(ssError)
      setLoading(false)
      return
    }
    try {
      const report = await rebalanceReport(profile)
      setRebalanceResult(report)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Rebalance report failed')
    } finally {
      setLoading(false)
    }
  }

  async function runAnnualReview() {
    setLoading(true)
    setError(null)
    setStressResults(null)
    setMonteCarloResult(null)
    setStrategyCompareResult(null)
    setResult(null)
    const ssError = validateProfileSocialSecurity(profile)
    if (ssError) {
      setError(ssError)
      setLoading(false)
      return
    }
    try {
      const prior = parsePriorYearReturn()
      const review = await annualReview(profile, prior)
      setAnnualReviewResult(review)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Annual review failed')
    } finally {
      setLoading(false)
    }
  }

  async function runAnnuityCompare() {
    setLoading(true)
    setError(null)
    setStressResults(null)
    setMonteCarloResult(null)
    setStrategyCompareResult(null)
    setAnnualReviewResult(null)
    setRebalanceResult(null)
    setSpendingCompareResult(null)
    setAnnuityCompareResult(null)
    setSafemaxResult(null)
    setResult(null)
    const ssError = validateProfileSocialSecurity(profile)
    if (ssError) {
      setError(ssError)
      setLoading(false)
      return
    }
    try {
      const scenario = buildScenarioOverrides('Annuity compare', 'base')
      const cmp = await annuityCompare(profile, { scenario, num_paths: 500 })
      setAnnuityCompareResult(cmp)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Annuity comparison failed')
    } finally {
      setLoading(false)
    }
  }

  async function runSafemaxReport() {
    setLoading(true)
    setError(null)
    setStressResults(null)
    setMonteCarloResult(null)
    setStrategyCompareResult(null)
    setAnnualReviewResult(null)
    setRebalanceResult(null)
    setSpendingCompareResult(null)
    setAnnuityCompareResult(null)
    setSafemaxResult(null)
    setResult(null)
    const ssError = validateProfileSocialSecurity(profile)
    if (ssError) {
      setError(ssError)
      setLoading(false)
      return
    }
    try {
      const report = await safemaxReport(profile, { num_paths: 200 })
      setSafemaxResult(report)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'SAFEMAX report failed')
    } finally {
      setLoading(false)
    }
  }

  async function runSpendingCompare() {
    setLoading(true)
    setError(null)
    setStressResults(null)
    setMonteCarloResult(null)
    setStrategyCompareResult(null)
    setAnnualReviewResult(null)
    setRebalanceResult(null)
    setSpendingCompareResult(null)
    setAnnuityCompareResult(null)
    setSafemaxResult(null)
    setResult(null)
    const ssError = validateProfileSocialSecurity(profile)
    if (ssError) {
      setError(ssError)
      setLoading(false)
      return
    }
    try {
      const scenario = buildScenarioOverrides('Spending compare', 'base')
      const cmp = await spendingCompare(profile, { scenario, num_paths: 500 })
      setSpendingCompareResult(cmp)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Spending scheme comparison failed')
    } finally {
      setLoading(false)
    }
  }

  async function runStrategyCompare() {
    setLoading(true)
    setError(null)
    setStressResults(null)
    setMonteCarloResult(null)
    setAnnualReviewResult(null)
    setRebalanceResult(null)
    setSpendingCompareResult(null)
    setAnnuityCompareResult(null)
    setSafemaxResult(null)
    setResult(null)
    const ssError = validateProfileSocialSecurity(profile)
    if (ssError) {
      setError(ssError)
      setLoading(false)
      return
    }
    try {
      const scenario = buildScenarioOverrides('Strategy compare', 'base')
      const cmp = await strategyCompare(profile, { scenario, num_paths: 500 })
      setStrategyCompareResult(cmp)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Strategy comparison failed')
    } finally {
      setLoading(false)
    }
  }

  const phase = result?.years[0]?.phase ?? '—'
  const debug = isDebugMode()

  return (
    <div className="min-h-screen w-full px-3 py-6 sm:px-4">
      <header className="mx-auto mb-8 max-w-[1600px] border-b border-slate-800 pb-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:gap-8">
          <img
            src="/logo.png"
            alt="247jeeves"
            width={530}
            height={330}
            className="h-[4.5rem] w-auto max-w-[min(100%,280px)] shrink-0 object-contain object-left sm:h-20"
          />
          <div className="min-w-0 flex-1">
            {debug && (
              <p className="text-sm font-medium text-brand">
                Phase 3e · CAPE / SAFEMAX, annuity, spending schemes & rebalance
              </p>
            )}
            <p className="mt-2 max-w-2xl text-slate-400">
              Your retirement tax butler — withdrawal sequencing, Roth conversions, and RMD
              forecasting. Educational model only; not tax advice.
            </p>
          </div>
        </div>
      </header>

      <div className="flex w-full flex-col gap-6">
        <section className="mx-auto w-full max-w-[1600px]">
          <h2 className="mb-4 text-lg font-semibold">{debug ? 'Your plan' : 'Your profile'}</h2>
          <ProfileForm profile={profile} onChange={setProfile} disabled={loading} debug={debug} />

          <div className="mt-4 grid max-w-3xl gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="text-sm text-slate-400">Market scenario</span>
              <select
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                value={returnScenario}
                disabled={loading}
                onChange={(e) => setReturnScenario(e.target.value as ReturnScenarioId)}
              >
                {RETURN_SCENARIOS.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-sm text-slate-400">
                Roth conversion / yr (blank = auto ~12% of trad. IRA)
              </span>
              <input
                type="number"
                min={0}
                step={1000}
                placeholder="e.g. 20000 for fixed; blank for auto"
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                value={rothOverride}
                disabled={loading}
                onChange={(e) => setRothOverride(e.target.value)}
              />
            </label>
            <label className="block sm:col-span-2">
              <span className="text-sm text-slate-400">Spending scheme for this run (optional)</span>
              <select
                className="mt-1 w-full max-w-md rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                value={spendingScenarioOverride}
                disabled={loading}
                onChange={(e) =>
                  setSpendingScenarioOverride(e.target.value as WithdrawalScheme | '')
                }
              >
                {spendingSchemeOptions(debug).map((s) => (
                  <option key={s.id || 'default'} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="mt-3 flex max-w-3xl items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={netPortfolioIncome}
              disabled={loading}
              onChange={(e) => setNetPortfolioIncome(e.target.checked)}
              className="rounded border-slate-600"
            />
            Net portfolio income against spending (dividends, rental, SS reduce account withdrawals)
          </label>

          <label className="mt-3 block max-w-md">
            <span className="text-sm text-slate-400">
              Prior year portfolio return for annual review (%, optional)
            </span>
            <input
              type="number"
              step={0.1}
              placeholder="e.g. 8 or -12 (percent)"
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
              value={priorYearReturn}
              disabled={loading}
              onChange={(e) => setPriorYearReturn(e.target.value)}
            />
          </label>

          {result?.summary.first_year_roth_conversion != null && rothOverride.trim() === '' && (
            <p className="mt-1 max-w-xl text-xs text-amber-400/90">
              Year 1 auto Roth conversion:{' '}
              {result.summary.first_year_roth_conversion.toLocaleString('en-US', {
                style: 'currency',
                currency: 'USD',
                maximumFractionDigits: 0,
              })}
              . Enter 20000 above to cap it.
            </p>
          )}

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={runSimulate}
              disabled={loading}
              className="rounded-lg bg-emerald-600 px-5 py-2.5 font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              {loading ? 'Running…' : 'Run simulation'}
            </button>
            <button
              type="button"
              onClick={runMonteCarlo}
              disabled={loading}
              className="rounded-lg border border-violet-700 bg-violet-950/40 px-4 py-2.5 text-sm text-violet-200 hover:bg-violet-900/40 disabled:opacity-50"
            >
              {loading ? 'Running…' : 'Run Monte Carlo (500 paths)'}
            </button>
            <button
              type="button"
              onClick={runAnnualReview}
              disabled={loading}
              className="rounded-lg border border-emerald-700 bg-emerald-950/40 px-4 py-2.5 text-sm text-emerald-200 hover:bg-emerald-900/40 disabled:opacity-50"
            >
              {loading ? 'Running…' : 'Run annual review'}
            </button>
            <button
              type="button"
              onClick={runRebalanceReport}
              disabled={loading}
              className="rounded-lg border border-sky-700 bg-sky-950/40 px-4 py-2.5 text-sm text-sky-200 hover:bg-sky-900/40 disabled:opacity-50"
            >
              {loading ? 'Running…' : 'Rebalance report'}
            </button>
            <button
              type="button"
              onClick={runSafemaxReport}
              disabled={loading}
              className="rounded-lg border border-indigo-700 bg-indigo-950/40 px-4 py-2.5 text-sm text-indigo-200 hover:bg-indigo-900/40 disabled:opacity-50"
            >
              {loading ? 'Running…' : 'CAPE / SAFEMAX report'}
            </button>
            <button
              type="button"
              onClick={runAnnuityCompare}
              disabled={loading}
              className="rounded-lg border border-amber-700 bg-amber-950/40 px-4 py-2.5 text-sm text-amber-200 hover:bg-amber-900/40 disabled:opacity-50"
            >
              {loading ? 'Running…' : debug ? 'Annuity vs book FA' : 'Annuity vs fixed spending'}
            </button>
            <button
              type="button"
              onClick={runSpendingCompare}
              disabled={loading}
              className="rounded-lg border border-violet-700 bg-violet-950/40 px-4 py-2.5 text-sm text-violet-200 hover:bg-violet-900/40 disabled:opacity-50"
            >
              {loading ? 'Running…' : 'Compare spending schemes'}
            </button>
            <button
              type="button"
              onClick={runStrategyCompare}
              disabled={loading}
              className="rounded-lg border border-amber-700 bg-amber-950/40 px-4 py-2.5 text-sm text-amber-200 hover:bg-amber-900/40 disabled:opacity-50"
            >
              {loading ? 'Running…' : 'Compare account withdrawal order'}
            </button>
            <button
              type="button"
              onClick={compareStressScenarios}
              disabled={loading}
              className="rounded-lg border border-emerald-700 bg-emerald-950/40 px-4 py-2.5 text-sm text-emerald-200 hover:bg-emerald-900/40 disabled:opacity-50"
            >
              Compare all market scenarios
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => {
                setResult(null)
                setStressResults(null)
                setMonteCarloResult(null)
                setStrategyCompareResult(null)
                setAnnualReviewResult(null)
                setRebalanceResult(null)
                setSpendingCompareResult(null)
                setAnnuityCompareResult(null)
                setSafemaxResult(null)
              }}
              className="rounded-lg border border-slate-600 px-4 py-2.5 text-sm text-slate-300 hover:bg-slate-800"
            >
              {debug ? 'New plan' : 'Reset'}
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => {
                setProfile(defaultSingleProfile)
                setResult(null)
                setStressResults(null)
                setMonteCarloResult(null)
                setStrategyCompareResult(null)
                setAnnualReviewResult(null)
    setRebalanceResult(null)
    setSpendingCompareResult(null)
    setAnnuityCompareResult(null)
    setSafemaxResult(null)
              }}
              className="rounded-lg border border-slate-600 px-4 py-2.5 text-sm text-slate-300 hover:bg-slate-800"
            >
              Single example
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => {
                setProfile(defaultProfile)
                setResult(null)
                setStressResults(null)
                setMonteCarloResult(null)
                setStrategyCompareResult(null)
                setAnnualReviewResult(null)
    setRebalanceResult(null)
    setSpendingCompareResult(null)
    setAnnuityCompareResult(null)
    setSafemaxResult(null)
              }}
              className="rounded-lg border border-slate-600 px-4 py-2.5 text-sm text-slate-300 hover:bg-slate-800"
            >
              Couple example
            </button>
          </div>
          {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
        </section>

        {safemaxResult && (
          <section className="mx-auto w-full max-w-[1600px]">
            <h2 className="mb-3 text-lg font-semibold">CAPE & SAFEMAX education</h2>
            <SafemaxReport result={safemaxResult} debug={debug} />
          </section>
        )}

        {annuityCompareResult && (
          <section className="mx-auto w-full max-w-[1600px]">
            <h2 className="mb-3 text-lg font-semibold">
              {debug ? 'Insurance annuity vs book FA' : 'Insurance annuity vs fixed spending'}
            </h2>
            <AnnuityComparison result={annuityCompareResult} debug={debug} />
          </section>
        )}

        {rebalanceResult && (
          <section className="mx-auto w-full max-w-[1600px]">
            <h2 className="mb-3 text-lg font-semibold">Target allocation & rebalance</h2>
            <RebalanceReport result={rebalanceResult} debug={debug} />
          </section>
        )}

        {annualReviewResult && (
          <section className="mx-auto w-full max-w-[1600px]">
            <h2 className="mb-3 text-lg font-semibold">Annual spending review</h2>
            <AnnualReview
              result={annualReviewResult}
              disabled={loading}
              debug={debug}
              onApplyRecommended={() => {
                setProfile({ ...profile, annual_spending: annualReviewResult.recommended_annual_spending })
              }}
            />
          </section>
        )}

        {spendingCompareResult && (
          <section className="mx-auto w-full max-w-[1600px]">
            <h2 className="mb-3 text-lg font-semibold">Spending scheme comparison</h2>
            <SpendingSchemeComparison result={spendingCompareResult} debug={debug} />
          </section>
        )}

        {strategyCompareResult && (
          <section className="mx-auto w-full max-w-[1600px]">
            <h2 className="mb-3 text-lg font-semibold">Account withdrawal order comparison</h2>
            <StrategyComparison result={strategyCompareResult} />
          </section>
        )}

        {monteCarloResult && (
          <section className="mx-auto w-full max-w-[1600px]">
            <h2 className="mb-3 text-lg font-semibold">Monte Carlo · sequence-of-returns risk</h2>
            <MonteCarloSummary result={monteCarloResult} />
            <div className="mt-4">
              <MonteCarloChart result={monteCarloResult} />
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Each path randomizes annual returns (normal distribution, clipped ±50%). Success =
              no year with unfunded spending. Uses your tax/withdrawal rules on every path.
            </p>
          </section>
        )}

        {stressResults && stressResults.length > 1 && (
          <section className="mx-auto w-full max-w-[1600px]">
            <h2 className="mb-3 text-lg font-semibold">Market scenario comparison</h2>
            <StressComparison results={stressResults} debug={debug} />
          </section>
        )}

        {result && (
          <>
            <section className="w-full">
              <div className="mb-3 flex flex-wrap items-center gap-3">
                <h2 className="text-lg font-semibold">Year-by-year projection</h2>
                {debug && (
                  <span className="rounded-full bg-slate-800 px-3 py-1 text-sm capitalize">
                    Phase: {phase.replace(/_/g, ' ')}
                  </span>
                )}
                {result.meta?.return_scenario && (
                  <span className="rounded-full bg-slate-800 px-3 py-1 text-sm">
                    Market: {String(result.meta.return_scenario).replace(/_/g, ' ')}
                  </span>
                )}
                {result.meta?.withdrawal_scheme && (
                  <span className="rounded-full bg-violet-950 px-3 py-1 text-sm text-violet-200">
                    Spend: {spendingSchemeLabel(String(result.meta.withdrawal_scheme), debug)}
                  </span>
                )}
                {result.years[0] && (
                  <span className="rounded-full bg-slate-800 px-3 py-1 text-sm text-slate-300">
                    Ages in run: You {result.years[0].age}
                    {result.years[0].spouse_age != null && ` · Sp ${result.years[0].spouse_age}`}
                  </span>
                )}
              </div>
              <SimulationTable years={result.years} debug={debug} />
            </section>

            <section className="mx-auto w-full max-w-[1600px]">
              <SummaryCards summary={result.summary} />
            </section>

            <section className="mx-auto grid w-full max-w-[1600px] gap-8 lg:grid-cols-2">
              <div>
                <h2 className="mb-3 text-lg font-semibold">This year&apos;s recommendations</h2>
                <Recommendations items={result.recommendations} debug={debug} />
              </div>
              <div>
                <h2 className="mb-3 text-lg font-semibold">Account balances over time</h2>
                <BalanceChart years={result.years} />
              </div>
            </section>
          </>
        )}

        {!result &&
          !stressResults &&
          !monteCarloResult &&
          !strategyCompareResult &&
          !annualReviewResult &&
          !rebalanceResult &&
          !spendingCompareResult &&
          !annuityCompareResult && (
          <p className="mx-auto w-full max-w-[1600px] text-slate-500">
            Enter your balances and run a simulation to see the year-by-year table, recommendations,
            and charts.
          </p>
        )}
      </div>
    </div>
  )
}

export default App
