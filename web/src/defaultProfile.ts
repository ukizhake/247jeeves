import type { Profile } from './types'

export const defaultSingleProfile: Profile = {
  name: 'Single Retiree',
  age: 62,
  plan_to_age: 95,
  filing_status: 'single',
  accounts: {
    traditional_ira: 800_000,
    roth_ira: 100_000,
    taxable: 400_000,
    cash: 50_000,
  },
  income: {
    rental: 0,
    dividends: 8_000,
    pension: 0,
    consulting: 0,
    other_ordinary: 0,
  },
  annual_spending: 72_000,
  social_security_claim_age: 70,
  social_security_annual_at_claim: 36_000,
  return_rate: 0.06,
  return_volatility: 0.15,
  inflation_rate: 0.03,
  withdrawal_scheme: 'performance_cola',
  annual_review_month: 10,
}

export const defaultProfile: Profile = {
  name: 'Retired Couple',
  age: 58,
  plan_to_age: 95,
  spouse_age: 62,
  projection_start_year: 2026,
  filing_status: 'mfj',
  accounts: {
    traditional_ira: 1_200_000,
    roth_ira: 50_000,
    taxable: 800_000,
    cash: 100_000,
  },
  income: {
    rental: 0,
    dividends: 15_000,
    pension: 0,
    consulting: 0,
    other_ordinary: 0,
  },
  annual_spending: 120_000,
  social_security_claim_age: 70,
  // Example: ssa.gov ~$3,999/mo at 70 → 3,999 × 12
  social_security_annual_at_claim: 47_988,
  spouse_social_security_annual_at_claim: 0,
  spouse_social_security_claim_age: 70,
  return_rate: 0.06,
  return_volatility: 0.15,
  inflation_rate: 0.03,
  withdrawal_scheme: 'performance_cola',
  annuity_income_annual: 0,
  annual_review_month: 10,
  performance_skip_cola_after_down_year: true,
}
