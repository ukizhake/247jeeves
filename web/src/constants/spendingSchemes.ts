import type { WithdrawalScheme } from '../types'

const PUBLIC_SCHEME_LABELS: Record<WithdrawalScheme, string> = {
  performance_cola: 'Performance COLA',
  cola: 'COLA',
  fixed_annuity: 'Fixed amount (nominal)',
  fixed_percentage: 'Fixed % of portfolio',
  floor_ceiling: 'Floor & ceiling',
}

const DEBUG_SCHEME_LABELS: Record<WithdrawalScheme, string> = {
  performance_cola: 'Performance COLA',
  cola: 'COLA',
  fixed_annuity: 'Book FA (nominal lifestyle)',
  fixed_percentage: 'Fixed % of portfolio (FP)',
  floor_ceiling: 'Floor & ceiling (F&C)',
}

export function spendingSchemeOptions(debug: boolean): {
  id: WithdrawalScheme | ''
  label: string
}[] {
  const labels = debug ? DEBUG_SCHEME_LABELS : PUBLIC_SCHEME_LABELS
  return [
    { id: '', label: 'Use profile default' },
    { id: 'performance_cola', label: labels.performance_cola },
    { id: 'cola', label: labels.cola },
    { id: 'fixed_annuity', label: labels.fixed_annuity },
    { id: 'fixed_percentage', label: labels.fixed_percentage },
    { id: 'floor_ceiling', label: labels.floor_ceiling },
  ]
}

/** @deprecated use spendingSchemeOptions(debug) */
export const SPENDING_SCHEME_OPTIONS = spendingSchemeOptions(false)

export function spendingSchemeLabel(scheme: string, debug = false): string {
  const labels = debug ? DEBUG_SCHEME_LABELS : PUBLIC_SCHEME_LABELS
  if (scheme in labels) return labels[scheme as WithdrawalScheme]
  return scheme.replace(/_/g, ' ')
}
