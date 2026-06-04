import type {
  AnnualReviewResponse,
  FidelityImportResult,
  RebalanceReportResponse,
  MonteCarloResponse,
  Profile,
  ProfileResponse,
  ScenarioOverrides,
  SimulateResponse,
  SpendingSchemeComparisonResponse,
  StrategyComparisonResponse,
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

export async function createProfile(profile: Profile): Promise<ProfileResponse> {
  const res = await fetch(`${API}/profiles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  })
  if (!res.ok) throw await apiError(res)
  return res.json()
}

export async function updateProfile(
  profileId: number,
  profile: Profile,
): Promise<ProfileResponse> {
  const res = await fetch(`${API}/profiles/${profileId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  })
  if (!res.ok) throw await apiError(res)
  return res.json()
}

export async function simulateProfile(
  profileId: number,
  scenario?: ScenarioOverrides,
): Promise<SimulateResponse> {
  const res = await fetch(`${API}/profiles/${profileId}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario: scenario ?? null }),
  })
  if (!res.ok) throw await apiError(res)
  return res.json()
}

export async function monteCarloProfile(
  profileId: number,
  options?: { scenario?: ScenarioOverrides; num_paths?: number; seed?: number },
): Promise<MonteCarloResponse> {
  const res = await fetch(`${API}/profiles/${profileId}/monte-carlo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scenario: options?.scenario ?? null,
      num_paths: options?.num_paths ?? 500,
      seed: options?.seed ?? null,
    }),
  })
  if (!res.ok) throw await apiError(res)
  return res.json()
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

export async function rebalanceReportProfile(profileId: number): Promise<RebalanceReportResponse> {
  const res = await fetch(`${API}/profiles/${profileId}/rebalance-report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  if (!res.ok) throw await apiError(res)
  return res.json()
}

export async function annualReviewProfile(
  profileId: number,
  priorYearReturn?: number | null,
): Promise<AnnualReviewResponse> {
  const res = await fetch(`${API}/profiles/${profileId}/annual-review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prior_year_return: priorYearReturn ?? null,
    }),
  })
  if (!res.ok) throw await apiError(res)
  return res.json()
}

export async function spendingCompareProfile(
  profileId: number,
  options?: { scenario?: ScenarioOverrides; num_paths?: number; seed?: number },
): Promise<SpendingSchemeComparisonResponse> {
  const res = await fetch(`${API}/profiles/${profileId}/spending-compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scenario: options?.scenario ?? null,
      num_paths: options?.num_paths ?? 500,
      seed: options?.seed ?? null,
    }),
  })
  if (!res.ok) throw await apiError(res)
  return res.json()
}

export async function strategyCompareProfile(
  profileId: number,
  options?: { scenario?: ScenarioOverrides; num_paths?: number; seed?: number },
): Promise<StrategyComparisonResponse> {
  const res = await fetch(`${API}/profiles/${profileId}/strategy-compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scenario: options?.scenario ?? null,
      num_paths: options?.num_paths ?? 500,
      seed: options?.seed ?? null,
    }),
  })
  if (!res.ok) throw await apiError(res)
  return res.json()
}
