"""SAFEMAX and Shiller CAPE education — Phase 3e (A Richer Retirement deck)."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from engine.models.profile import Profile, ScenarioOverrides
from engine.monte_carlo import MonteCarloConfig, run_monte_carlo
from engine.simulator import projection_horizon_years
from engine.withdrawals.annuity import total_wealth as _total_wealth

UNIVERSAL_RULE_PCT = 0.047
DEFAULT_CAPE = 28.0
ANCHORS_PATH = Path(__file__).resolve().parent / "data" / "cape_safemax_anchors.json"


class CapeSafemaxAnchor(BaseModel):
    cape: float
    safemax: float
    retirement_date: str = ""
    note: str = ""


class SafemaxReport(BaseModel):
    shiller_cape: float
    cape_source: str
    planning_horizon_years: int
    estimated_safemax_pct: float
    estimated_safemax_dollars: float
    universal_rule_pct: float
    current_implied_iwr_pct: float
    current_annual_spending: float
    spending_gap_vs_estimate: float
    inflation_regime: str
    horizon_adjustment_note: str
    valuation_band: str
    nearby_anchors: list[CapeSafemaxAnchor]
    suggestions: list[str] = Field(default_factory=list)
    mc_paths: int = 0
    mc_success_at_current_spending: float | None = None
    mc_success_at_estimated_safemax: float | None = None
    mc_median_wealth_at_current: float | None = None
    mc_median_wealth_at_estimated: float | None = None


def _load_anchors() -> list[CapeSafemaxAnchor]:
    raw = json.loads(ANCHORS_PATH.read_text())
    return [CapeSafemaxAnchor.model_validate(row) for row in raw]


def _interpolate_safemax(cape: float, anchors: list[CapeSafemaxAnchor]) -> float:
    """Piecewise linear SAFEMAX vs CAPE (30yr COLA, 55/40/5 — deck stalwart config)."""
    points = sorted(anchors, key=lambda a: a.cape)
    if cape <= points[0].cape:
        return points[0].safemax
    if cape >= points[-1].cape:
        excess = cape - points[-1].cape
        return max(0.04, points[-1].safemax - 0.001 * excess)
    for i in range(len(points) - 1):
        lo, hi = points[i], points[i + 1]
        if lo.cape <= cape <= hi.cape:
            t = (cape - lo.cape) / (hi.cape - lo.cape)
            return lo.safemax + t * (hi.safemax - lo.safemax)
    return points[-1].safemax


def _horizon_factor(horizon_years: int, base_horizon: int = 30) -> tuple[float, str]:
    """Longer horizons → lower sustainable initial rate (deck Fig. planning horizon)."""
    if horizon_years <= base_horizon:
        return 1.0, f"Base estimate uses {base_horizon}-year deck longevity."
    extra = horizon_years - base_horizon
    # ~0.15% absolute reduction per 5 years beyond 30
    reduction = 0.0015 * (extra / 5)
    factor = max(0.75, 1.0 - reduction / 0.07)
    return factor, (
        f"Horizon {horizon_years}y vs deck {base_horizon}y — rate scaled down ~{reduction * 100:.1f}%."
    )


def _inflation_adjustment(regime: str, rate: float) -> tuple[float, str]:
    if regime == "high":
        adjusted = max(0.04, rate - 0.01)
        return adjusted, "High-inflation regime adjustment: −1.0% vs normal (deck)."
    return rate, "Normal inflation regime (deck default)."


def _valuation_band(cape: float) -> str:
    if cape < 12:
        return "low"
    if cape < 18:
        return "moderate"
    if cape < 25:
        return "elevated"
    return "high"


def _nearest_anchors(cape: float, anchors: list[CapeSafemaxAnchor], n: int = 3) -> list[CapeSafemaxAnchor]:
    return sorted(anchors, key=lambda a: abs(a.cape - cape))[:n]


def resolve_cape(profile: Profile) -> tuple[float, str]:
    if profile.shiller_cape is not None and profile.shiller_cape > 0:
        return profile.shiller_cape, "profile"
    return DEFAULT_CAPE, "default_assumption"


def estimate_safemax_rate(
    profile: Profile,
    *,
    horizon_years: int | None = None,
) -> tuple[float, str, list[CapeSafemaxAnchor]]:
    anchors = _load_anchors()
    cape, cape_src = resolve_cape(profile)
    base = _interpolate_safemax(cape, anchors)
    horizon = horizon_years or (profile.plan_to_age - profile.age + 1)
    h_factor, h_note = _horizon_factor(horizon)
    rate, inf_note = _inflation_adjustment(profile.inflation_regime, base * h_factor)
    rate = max(0.04, min(0.12, rate))
    note = f"{h_note} {inf_note}"
    return rate, note, _nearest_anchors(cape, anchors)


def compute_safemax_report(
    profile: Profile,
    scenario: ScenarioOverrides | None = None,
    *,
    run_mc_validation: bool = True,
    mc_paths: int = 200,
) -> SafemaxReport:
    """
    Educational SAFEMAX vs CAPE report — not a guarantee, historical deck methodology.
    """
    scenario = scenario or ScenarioOverrides()
    wealth = _total_wealth(profile.accounts)
    horizon = projection_horizon_years(profile, scenario)
    cape, cape_source = resolve_cape(profile)
    rate, adj_note, nearby = estimate_safemax_rate(profile, horizon_years=horizon)
    est_dollars = wealth * rate
    port_inc = (
        profile.income.rental
        + profile.income.dividends
        + profile.income.pension
        + profile.income.consulting
        + profile.income.other_ordinary
        + profile.annuity_income_annual
    )
    port_wd = max(0.0, profile.annual_spending - port_inc)
    current_iwr = (port_wd / wealth) if wealth > 0 else 0.0

    band = _valuation_band(cape)
    suggestions: list[str] = []

    suggestions.append(
        "SAFEMAX is the highest year-one withdrawal rate that survived a 30-year historical "
        "path for that retiree — personal, not universal."
    )
    suggestions.append(
        f"Universal “4.7% rule” ({UNIVERSAL_RULE_PCT * 100:.1f}%) is the worst-case across all "
        "historical retirees in the deck — most people could start higher."
    )
    if cape >= 25:
        suggestions.append(
            "High Shiller CAPE historically preceded major bear markets — consider conservative "
            "starting withdrawals or flexible spending (performance COLA / F&C)."
        )
    elif cape <= 12:
        suggestions.append(
            "Low CAPE (cheap stocks) historically allowed higher starting withdrawal rates — "
            "but timing the market is unreliable."
        )
    if current_iwr > rate + 0.005:
        suggestions.append(
            f"Your implied portfolio IWR ({current_iwr * 100:.2f}%) is above the CAPE-based "
            f"estimate ({rate * 100:.2f}%) — run Monte Carlo before raising spending."
        )
    elif current_iwr < rate - 0.01:
        suggestions.append(
            f"Your implied IWR ({current_iwr * 100:.2f}%) is below the CAPE estimate — you may "
            "have room to increase lifestyle spending if other goals allow."
        )

    mc_current = mc_est = mc_wealth_cur = mc_wealth_est = None
    if run_mc_validation and wealth > 0 and horizon >= 5:
        config = MonteCarloConfig(num_paths=mc_paths, seed=42)
        result_cur = run_monte_carlo(profile, scenario, config)
        spend_at_est = port_inc + wealth * rate
        profile_est = profile.model_copy(update={"annual_spending": round(spend_at_est, 2)})
        result_est = run_monte_carlo(profile_est, scenario, config)
        mc_current = result_cur.success_rate
        mc_est = result_est.success_rate
        mc_wealth_cur = result_cur.median_final_wealth
        mc_wealth_est = result_est.median_final_wealth

    return SafemaxReport(
        shiller_cape=round(cape, 2),
        cape_source=cape_source,
        planning_horizon_years=horizon,
        estimated_safemax_pct=round(rate, 4),
        estimated_safemax_dollars=round(est_dollars, 2),
        universal_rule_pct=UNIVERSAL_RULE_PCT,
        current_implied_iwr_pct=round(current_iwr, 4),
        current_annual_spending=round(profile.annual_spending, 2),
        spending_gap_vs_estimate=round(profile.annual_spending - est_dollars, 2),
        inflation_regime=profile.inflation_regime,
        horizon_adjustment_note=adj_note,
        valuation_band=band,
        nearby_anchors=nearby,
        suggestions=suggestions,
        mc_paths=mc_paths if run_mc_validation else 0,
        mc_success_at_current_spending=mc_current,
        mc_success_at_estimated_safemax=mc_est,
        mc_median_wealth_at_current=mc_wealth_cur,
        mc_median_wealth_at_estimated=mc_wealth_est,
    )
