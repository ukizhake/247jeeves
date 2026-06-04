"""Withdrawal spending paths — COLA, fixed annuity, performance-based (Phase 3a)."""

from __future__ import annotations

from enum import Enum

from engine.models.profile import Profile


class WithdrawalScheme(str, Enum):
    COLA = "cola"
    FIXED_ANNUITY = "fixed_annuity"
    PERFORMANCE_COLA = "performance_cola"


def cola_rate(profile: Profile) -> float:
    if profile.spending_cola_rate is not None:
        return profile.spending_cola_rate
    return profile.inflation_rate


def annuity_income_year(profile: Profile, year_index: int) -> float:
    base = profile.annuity_income_annual
    if base <= 0:
        return 0.0
    rate = profile.annuity_cola_rate if profile.annuity_cola_rate is not None else 0.0
    return base * ((1 + rate) ** year_index)


def spending_for_year(
    profile: Profile,
    year_index: int,
    *,
    base_annual: float,
    prior_spending: float,
    prior_year_return: float | None,
) -> tuple[float, str]:
    """
    Compute inflation-adjusted or scheme-specific spending for a projection year.
    Returns (amount, note) explaining adjustments.
    """
    scheme = WithdrawalScheme(profile.withdrawal_scheme)
    rate = cola_rate(profile)

    if year_index == 0:
        return base_annual, f"{scheme.value}: year-one spending"

    if scheme == WithdrawalScheme.FIXED_ANNUITY:
        return base_annual, "Fixed annuity scheme: nominal spending unchanged"

    cola_spending = prior_spending * (1 + rate)

    if scheme == WithdrawalScheme.COLA:
        return cola_spending, f"COLA +{rate * 100:.1f}%"

    # performance_cola
    if (
        profile.performance_skip_cola_after_down_year
        and prior_year_return is not None
        and prior_year_return < 0
    ):
        adjusted = prior_spending
        note = (
            f"Performance rule: portfolio down {prior_year_return * 100:.1f}% — "
            "spending held flat (no COLA bump)"
        )
    else:
        adjusted = cola_spending
        note = f"COLA +{rate * 100:.1f}%"
        if prior_year_return is not None and prior_year_return >= 0:
            note += f" (portfolio up {prior_year_return * 100:.1f}%)"

    if profile.performance_max_raise_pct is not None and adjusted > prior_spending:
        cap = prior_spending * (1 + profile.performance_max_raise_pct)
        if adjusted > cap:
            adjusted = cap
            note += f"; raise capped at {profile.performance_max_raise_pct * 100:.0f}%"

    if profile.performance_max_cut_pct is not None and adjusted < prior_spending:
        floor = prior_spending * (1 - profile.performance_max_cut_pct)
        if adjusted < floor:
            adjusted = floor
            note += f"; cut capped at {profile.performance_max_cut_pct * 100:.0f}%"

    return adjusted, note
