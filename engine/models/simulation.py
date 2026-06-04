from typing import Any, Optional

from pydantic import BaseModel, Field


class YearState(BaseModel):
    year: int
    age: int
    spouse_age: Optional[int] = None
    phase: str

    traditional_ira: float
    roth_ira: float
    taxable: float
    cash: float

    withdrawal_taxable: float = 0
    withdrawal_ira: float = 0
    withdrawal_roth: float = 0
    roth_conversion: float = 0

    rental_income: float = 0
    fund_income: float = 0
    consulting_income: float = 0
    pension_income: float = 0
    total_income: float = 0
    portfolio_income: float = 0
    spending_target: float = 0
    annuity_income: float = 0
    spending_adjustment_note: str = ""
    implied_withdrawal_rate: float = 0
    withdrawal_need: float = 0
    unfunded_spending: float = 0
    return_rate_applied: float = 0
    other_income: float = 0
    social_security: float = 0
    primary_social_security: float = 0
    spouse_social_security: float = 0
    social_security_taxable: float = 0
    ordinary_income: float = 0
    long_term_capital_gains: float = 0
    withdrawal_taxable_basis: float = 0
    withdrawal_taxable_gain: float = 0
    total_deductions: float = 0
    agi: float = 0
    taxable_income: float = 0
    federal_tax: float = 0
    ltcg_tax: float = 0
    niit_tax: float = 0
    niit_warning: bool = False

    rmd_required: float = 0
    rmd_taken: float = 0

    marginal_rate: float = 0
    bracket_room_12: float = 0
    bracket_room_22: float = 0
    bracket_room_24: float = 0

    irmaa_warning: bool = False
    aca_cliff_warning: bool = False


class ActionRecommendation(BaseModel):
    type: str
    account: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None


class Recommendation(BaseModel):
    rule_id: str
    priority: int = 50
    title: str
    phase: str
    actions: list[ActionRecommendation] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    rationale: str = ""


class SimulationSummary(BaseModel):
    rmd_at_age_75: float = 0
    ira_balance_at_age_75: float = 0
    lifetime_federal_tax: float = 0
    lifetime_niit: float = 0
    first_year_total_deductions: float = 0
    first_year_taxable_ss: float = 0
    first_year_social_security: float = 0
    first_year_roth_conversion: float = 0
    final_traditional_ira: float = 0
    final_total_wealth: float = 0


class SimulationResult(BaseModel):
    years: list[YearState]
    recommendations: list[Recommendation]
    summary: SimulationSummary
    meta: dict[str, Any] = Field(default_factory=dict)


class MonteCarloYearBand(BaseModel):
    year: int
    age: int
    p10: float
    p50: float
    p90: float


class MonteCarloResult(BaseModel):
    num_paths: int
    success_rate: float
    median_final_wealth: float
    p10_final_wealth: float
    p90_final_wealth: float
    mean_return: float
    return_volatility: float
    year_bands: list[MonteCarloYearBand]
    meta: dict[str, Any] = Field(default_factory=dict)


class StrategySummary(BaseModel):
    policy: str
    label: str
    success_rate: float
    median_final_wealth: float
    p10_final_wealth: float
    p90_final_wealth: float
    median_lifetime_tax: float


class StrategyComparisonResult(BaseModel):
    num_paths: int
    seed: int | None
    mean_return: float
    return_volatility: float
    strategies: list[StrategySummary]
    meta: dict[str, Any] = Field(default_factory=dict)


class SpendingSchemeSummary(BaseModel):
    scheme: str
    label: str
    success_rate: float
    median_final_wealth: float
    p10_final_wealth: float
    p90_final_wealth: float
    median_lifetime_spending: float
    median_lifetime_tax: float


class SpendingSchemeComparisonResult(BaseModel):
    num_paths: int
    seed: int | None
    mean_return: float
    return_volatility: float
    schemes: list[SpendingSchemeSummary]
    meta: dict[str, Any] = Field(default_factory=dict)
