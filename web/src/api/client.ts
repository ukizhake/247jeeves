import type {
  AnnuityComparisonResult,
  AnnualReviewResult,
  FidelityImportResult,
  MonteCarloResult,
  Profile,
  RebalanceReportResult,
  SafemaxReportResult,
  ScenarioOverrides,
  SimulationResult,
  SpendingSchemeComparisonResult,
  StrategyComparisonResult,
} from '../types'

const API = import.meta.env.VITE_API_BASE ?? '/api'

async function apiError(res: Response): Promise<Error> {
  const text = await res.text()
  if (res.status === 404) {
    return new Error(
      'API not found. Start the backend: PYTHONPATH=. uvicorn api.main:app --reload --port 8888',
    )
  }
  try {
    const json = JSON.parse(text) as {
      detail?: string | Array<{ msg?: string; loc?: string[] }>
    }
    if (Array.isArray(json.detail)) {
      const messages = json.detail
        .map((d) => d.msg?.replace(/^Value error, /, '') ?? '')
        .filter(Boolean)
      if (messages.length) return new Error(messages.join(' '))
    }
    if (typeof json.detail === 'string') return new Error(json.detail)
  } catch {
    /* plain text */
  }
  return new Error(text || `Request failed (${res.status})`)
}

async function postCompute<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}/compute${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw await apiError(res)
  return res.json() as Promise<T>
}

export async function simulate(
  profile: Profile,
  scenario?: ScenarioOverrides,
): Promise<SimulationResult> {
  const data = await postCompute<{ result: SimulationResult }>('/simulate', {
    profile,
    scenario: scenario ?? null,
  })
  return data.result
}

export async function monteCarlo(
  profile: Profile,
  options?: { scenario?: ScenarioOverrides; num_paths?: number; seed?: number },
): Promise<MonteCarloResult> {
  const data = await postCompute<{ result: MonteCarloResult }>('/monte-carlo', {
    profile,
    scenario: options?.scenario ?? null,
    num_paths: options?.num_paths ?? 500,
    seed: options?.seed ?? null,
  })
  return data.result
}

export async function importFidelityCsv(file: File): Promise<FidelityImportResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API}/import/fidelity`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw await apiError(res)
  const data = (await res.json()) as { result: FidelityImportResult }
  return data.result
}

export async function rebalanceReport(profile: Profile): Promise<RebalanceReportResult> {
  const data = await postCompute<{ result: RebalanceReportResult }>('/rebalance-report', {
    profile,
  })
  return data.result
}

export async function annualReview(
  profile: Profile,
  priorYearReturn?: number | null,
): Promise<AnnualReviewResult> {
  const data = await postCompute<{ result: AnnualReviewResult }>('/annual-review', {
    profile,
    prior_year_return: priorYearReturn ?? null,
  })
  return data.result
}

export async function safemaxReport(
  profile: Profile,
  options?: { run_mc_validation?: boolean; num_paths?: number },
): Promise<SafemaxReportResult> {
  const data = await postCompute<{ result: SafemaxReportResult }>('/safemax-report', {
    profile,
    run_mc_validation: options?.run_mc_validation ?? true,
    num_paths: options?.num_paths ?? 200,
  })
  return data.result
}

export async function annuityCompare(
  profile: Profile,
  options?: { scenario?: ScenarioOverrides; num_paths?: number; seed?: number },
): Promise<AnnuityComparisonResult> {
  const data = await postCompute<{ result: AnnuityComparisonResult }>('/annuity-compare', {
    profile,
    scenario: options?.scenario ?? null,
    num_paths: options?.num_paths ?? 500,
    seed: options?.seed ?? null,
  })
  return data.result
}

export async function spendingCompare(
  profile: Profile,
  options?: { scenario?: ScenarioOverrides; num_paths?: number; seed?: number },
): Promise<SpendingSchemeComparisonResult> {
  const data = await postCompute<{ result: SpendingSchemeComparisonResult }>('/spending-compare', {
    profile,
    scenario: options?.scenario ?? null,
    num_paths: options?.num_paths ?? 500,
    seed: options?.seed ?? null,
  })
  return data.result
}

export async function strategyCompare(
  profile: Profile,
  options?: { scenario?: ScenarioOverrides; num_paths?: number; seed?: number },
): Promise<StrategyComparisonResult> {
  const data = await postCompute<{ result: StrategyComparisonResult }>('/strategy-compare', {
    profile,
    scenario: options?.scenario ?? null,
    num_paths: options?.num_paths ?? 500,
    seed: options?.seed ?? null,
  })
  return data.result
}
