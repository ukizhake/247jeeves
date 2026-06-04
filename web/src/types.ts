export type FilingStatus = 'single' | 'mfj'

export type WithdrawalScheme = 'cola' | 'fixed_annuity' | 'performance_cola'

export interface AssetAllocation {
  stocks: number
  bonds: number
  cash: number
}

export interface Accounts {
  traditional_ira: number
  roth_ira: number
  taxable: number
  cash: number
}

export interface IncomeSources {
  rental: number
  dividends: number
  pension: number
  consulting: number
  other_ordinary?: number
  qualified_dividend_ratio?: number
}

export interface Profile {
  name: string
  age: number
  plan_to_age?: number
  spouse_age?: number
  filing_status: FilingStatus
  accounts: Accounts
  income?: IncomeSources
  annual_spending: number
  social_security_claim_age: number
  social_security_annual_at_claim: number
  spouse_social_security_annual_at_claim?: number
  spouse_social_security_claim_age?: number
  social_security_cola_rate?: number | null
  projection_start_year?: number
  return_rate: number
  return_volatility?: number
  inflation_rate: number
  withdrawal_scheme?: WithdrawalScheme
  spending_cola_rate?: number | null
  annuity_income_annual?: number
  annuity_cola_rate?: number | null
  annual_review_month?: number
  performance_skip_cola_after_down_year?: boolean
  performance_max_raise_pct?: number | null
  performance_max_cut_pct?: number | null
  taxable_cost_basis_ratio?: number
  target_allocation?: AssetAllocation
  current_allocation?: AssetAllocation | null
  rebalance_band_pct?: number
}

export interface ScenarioOverrides {
  name?: string
  horizon_years?: number
  roth_conversion_annual?: number | null
  spending_override?: number | null
  target_bracket_rate?: number
  return_scenario?: 'base' | 'bad_early' | 'flat_low'
  net_portfolio_income?: boolean
  withdrawal_policy?: 'phase_default' | 'taxable_first' | 'cash_first' | 'ira_first'
}

export interface YearState {
  year: number
  age: number
  spouse_age?: number
  phase: string
  traditional_ira: number
  roth_ira: number
  taxable: number
  federal_tax: number
  ltcg_tax?: number
  niit_tax?: number
  niit_warning?: boolean
  social_security_taxable?: number
  social_security?: number
  primary_social_security?: number
  spouse_social_security?: number
  roth_conversion: number
  withdrawal_taxable: number
  withdrawal_ira: number
  withdrawal_roth?: number
  cash?: number
  taxable_income?: number
  rmd_required: number
  marginal_rate: number
  rental_income?: number
  fund_income?: number
  consulting_income?: number
  pension_income?: number
  total_income?: number
  portfolio_income?: number
  spending_target?: number
  annuity_income?: number
  spending_adjustment_note?: string
  implied_withdrawal_rate?: number
  withdrawal_need?: number
  return_rate_applied?: number
  total_deductions?: number
  ordinary_income?: number
  long_term_capital_gains?: number
  withdrawal_taxable_basis?: number
  withdrawal_taxable_gain?: number
  agi?: number
}

export interface ActionRecommendation {
  type: string
  account?: string
  amount?: number
  note?: string
}

export interface Recommendation {
  rule_id: string
  priority: number
  title: string
  phase: string
  actions: ActionRecommendation[]
  tradeoffs: string[]
  rationale: string
}

export interface SimulationSummary {
  rmd_at_age_75: number
  ira_balance_at_age_75: number
  lifetime_federal_tax: number
  lifetime_niit?: number
  first_year_total_deductions?: number
  first_year_taxable_ss?: number
  first_year_social_security?: number
  first_year_roth_conversion?: number
  final_traditional_ira?: number
  final_total_wealth: number
}

export interface SimulationResult {
  years: YearState[]
  recommendations: Recommendation[]
  summary: SimulationSummary
  meta?: Record<string, string | number | boolean>
}

export interface MonteCarloYearBand {
  year: number
  age: number
  p10: number
  p50: number
  p90: number
}

export interface MonteCarloResult {
  num_paths: number
  success_rate: number
  median_final_wealth: number
  p10_final_wealth: number
  p90_final_wealth: number
  mean_return: number
  return_volatility: number
  year_bands: MonteCarloYearBand[]
  meta?: Record<string, string | number | boolean | null>
}

export interface StrategySummary {
  policy: string
  label: string
  success_rate: number
  median_final_wealth: number
  p10_final_wealth: number
  p90_final_wealth: number
  median_lifetime_tax: number
}

export interface StrategyComparisonResult {
  num_paths: number
  seed: number | null
  mean_return: number
  return_volatility: number
  strategies: StrategySummary[]
  meta?: Record<string, string | number | boolean | null>
}

export interface StrategyComparisonResponse {
  profile_id: number
  result: StrategyComparisonResult
}

export interface AnnualReviewResult {
  review_month: number
  review_month_name: string
  withdrawal_scheme: string
  current_annual_spending: number
  recommended_annual_spending: number
  cola_rate_applied: number
  cola_dollar_change: number
  annuity_income: number
  total_wealth: number
  implied_withdrawal_rate: number
  portfolio_income_estimate: number
  portfolio_withdrawal_estimate: number
  prior_year_return: number | null
  performance_note: string
  suggestions: string[]
}

export interface AnnualReviewResponse {
  profile_id: number
  result: AnnualReviewResult
}

export interface AllocationSlice {
  asset: string
  target_pct: number
  current_pct: number
  target_dollars: number
  current_dollars: number
  drift_dollars: number
  drift_pct: number
}

export interface RebalanceTrade {
  asset: string
  action: string
  amount: number
  preferred_location: string
}

export interface RebalanceReportResult {
  total_wealth: number
  tax_advantaged_balance: number
  taxable_balance: number
  cash_balance: number
  target: AssetAllocation
  current: AssetAllocation
  slices: AllocationSlice[]
  trades: RebalanceTrade[]
  max_drift_pct: number
  needs_rebalance: boolean
  rebalance_in_tax_advantaged: number
  rebalance_notes: string[]
  suggestions: string[]
}

export interface RebalanceReportResponse {
  profile_id: number
  result: RebalanceReportResult
}

export interface MonteCarloResponse {
  profile_id: number
  result: MonteCarloResult
}

export interface SimulateResponse {
  profile_id: number
  result: SimulationResult
}

export interface ProfileResponse {
  id: number
  profile: Profile
}

export interface FidelityAccountSummary {
  account_number: string
  account_name: string
  bucket: 'taxable' | 'traditional_ira' | 'roth_ira' | 'cash' | 'unknown'
  total_value: number
  cost_basis: number
}

export interface FidelityHolding {
  account_number: string
  account_name: string
  symbol: string
  description: string
  quantity: number
  current_value: number
  cost_basis: number
  bucket: FidelityAccountSummary['bucket']
}

export interface FidelityImportResult {
  as_of: string | null
  accounts: FidelityAccountSummary[]
  holdings: FidelityHolding[]
  traditional_ira: number
  roth_ira: number
  taxable: number
  cash: number
  taxable_cost_basis_ratio: number
  total_value: number
  position_count: number
}
