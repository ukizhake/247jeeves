"""Annual spending review — COLA, annuity, performance rules (Phase 3a)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from engine.models.profile import Profile
from engine.withdrawals.spending import (
    WithdrawalScheme,
    annuity_income_year,
    cola_rate,
    effective_withdrawal_rate,
    spending_for_year,
)


MONTH_NAMES = (
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


class AnnualReviewResult(BaseModel):
    review_month: int
    review_month_name: str
    withdrawal_scheme: str
    current_annual_spending: float
    recommended_annual_spending: float
    cola_rate_applied: float
    cola_dollar_change: float
    annuity_income: float
    total_wealth: float
    implied_withdrawal_rate: float
    portfolio_income_estimate: float
    portfolio_withdrawal_estimate: float
    prior_year_return: float | None
    performance_note: str
    suggestions: list[str] = Field(default_factory=list)


def total_wealth(profile: Profile) -> float:
    a = profile.accounts
    return a.traditional_ira + a.roth_ira + a.taxable + a.cash


def portfolio_income_year0(profile: Profile) -> float:
    inc = profile.income
    return inc.rental + inc.dividends + inc.pension + inc.consulting + inc.other_ordinary


def compute_annual_review(
    profile: Profile,
    *,
    prior_year_return: float | None = None,
    year_index: int = 0,
) -> AnnualReviewResult:
    """
    Suggest next-year spending for the annual review ritual (e.g. each October).
    year_index=0 uses profile.annual_spending as the current baseline.
    """
    current = profile.annual_spending
    wealth = total_wealth(profile)
    if profile.withdrawal_scheme == WithdrawalScheme.FIXED_PERCENTAGE.value:
        iwr = effective_withdrawal_rate(profile, wealth=wealth, base_annual=current)
        recommended = wealth * iwr
        perf_note = f"FP next year: {iwr * 100:.2f}% of portfolio (${wealth:,.0f})"
    else:
        recommended, perf_note = spending_for_year(
            profile,
            year_index + 1,
            base_annual=current,
            prior_spending=current,
            prior_year_return=prior_year_return,
            wealth_start=wealth,
        )
    annuity = annuity_income_year(profile, year_index + 1)
    port_inc = portfolio_income_year0(profile)
    port_wd = max(0.0, recommended - port_inc - annuity)
    iwr = (port_wd / wealth) if wealth > 0 else 0.0
    rate = cola_rate(profile)
    month = profile.annual_review_month

    suggestions: list[str] = []
    if profile.withdrawal_scheme == WithdrawalScheme.PERFORMANCE_COLA.value:
        suggestions.append(
            "Performance COLA: inflate spending after good years; hold flat after a down year."
        )
    elif profile.withdrawal_scheme == WithdrawalScheme.FIXED_ANNUITY.value:
        suggestions.append(
            "Fixed annuity scheme: keep the same nominal spending; does not adjust for inflation."
        )
    elif profile.withdrawal_scheme == WithdrawalScheme.FIXED_PERCENTAGE.value:
        suggestions.append(
            "Fixed % scheme: spending rises and falls with portfolio value — volatile income, capital preservation."
        )
    if annuity > 0:
        suggestions.append(
            f"Annuity/pension floor covers ${annuity:,.0f}/yr — reduces portfolio withdrawals."
        )
    if prior_year_return is not None and prior_year_return < -0.1:
        suggestions.append(
            "Portfolio had a double-digit decline — consider conservative spending even if rules allow a raise."
        )
    if iwr > 0.05:
        suggestions.append(
            f"Implied portfolio withdrawal rate {iwr * 100:.1f}% is above a typical 4–5% starting rate — run Monte Carlo."
        )

    return AnnualReviewResult(
        review_month=month,
        review_month_name=MONTH_NAMES[month] if 1 <= month <= 12 else "October",
        withdrawal_scheme=profile.withdrawal_scheme,
        current_annual_spending=round(current, 2),
        recommended_annual_spending=round(recommended, 2),
        cola_rate_applied=rate,
        cola_dollar_change=round(recommended - current, 2),
        annuity_income=round(annuity, 2),
        total_wealth=round(wealth, 2),
        implied_withdrawal_rate=round(iwr, 4),
        portfolio_income_estimate=round(port_inc, 2),
        portfolio_withdrawal_estimate=round(port_wd, 2),
        prior_year_return=prior_year_return,
        performance_note=perf_note,
        suggestions=suggestions,
    )
