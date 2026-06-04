import type { WithdrawalScheme } from '../types'

export const SPENDING_SCHEME_OPTIONS: {
  id: WithdrawalScheme | ''
  label: string
}[] = [
  { id: '', label: 'Use profile default' },
  { id: 'performance_cola', label: 'Performance COLA' },
  { id: 'cola', label: 'COLA' },
  { id: 'fixed_annuity', label: 'Fixed nominal (FA)' },
  { id: 'fixed_percentage', label: 'Fixed % of portfolio (FP)' },
]

export function spendingSchemeLabel(scheme: string): string {
  return SPENDING_SCHEME_OPTIONS.find((s) => s.id === scheme)?.label ?? scheme.replace(/_/g, ' ')
}
