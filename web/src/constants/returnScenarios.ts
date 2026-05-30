export type ReturnScenarioId = 'base' | 'bad_early' | 'flat_low'

export const RETURN_SCENARIOS: { id: ReturnScenarioId; label: string }[] = [
  { id: 'base', label: 'Base — your expected return every year' },
  {
    id: 'bad_early',
    label: 'Bad early decade (−15%, −10%, −5%, then recovery to base)',
  },
  { id: 'flat_low', label: 'Flat / low — 2% for 10 years, then base' },
]
