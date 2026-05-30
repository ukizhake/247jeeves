"""Monte Carlo retirement simulation."""

import pytest

from engine.monte_carlo import MonteCarloConfig, run_monte_carlo
from engine.models.profile import FilingStatus, Profile, ScenarioOverrides


def _wealthy_profile(**kwargs) -> Profile:
    defaults = dict(
        name="mc",
        age=58,
        plan_to_age=90,
        filing_status=FilingStatus.MFJ,
        accounts={
            "traditional_ira": 2_000_000,
            "roth_ira": 500_000,
            "taxable": 1_500_000,
            "cash": 100_000,
        },
        income={"dividends": 40_000, "rental": 0},
        annual_spending=120_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        return_rate=0.06,
        return_volatility=0.15,
        inflation_rate=0.03,
    )
    defaults.update(kwargs)
    return Profile(**defaults)


def test_monte_carlo_reproducible_with_seed():
    p = _wealthy_profile()
    s = ScenarioOverrides(horizon_years=10, roth_conversion_annual=0)
    a = run_monte_carlo(p, s, MonteCarloConfig(num_paths=100, seed=42))
    b = run_monte_carlo(p, s, MonteCarloConfig(num_paths=100, seed=42))
    assert a.success_rate == b.success_rate
    assert a.median_final_wealth == b.median_final_wealth
    assert len(a.year_bands) == 10


def test_monte_carlo_success_rate_bounds():
    p = _wealthy_profile()
    result = run_monte_carlo(
        p,
        ScenarioOverrides(horizon_years=15, roth_conversion_annual=0),
        MonteCarloConfig(num_paths=200, seed=1),
    )
    assert 0.0 <= result.success_rate <= 1.0
    assert result.p10_final_wealth <= result.median_final_wealth <= result.p90_final_wealth
    assert result.num_paths == 200


def test_high_volatility_lowers_success_vs_zero_vol():
    p = _wealthy_profile(return_volatility=0.0)
    s = ScenarioOverrides(horizon_years=20, roth_conversion_annual=0, net_portfolio_income=True)
    stable = run_monte_carlo(
        p,
        s,
        MonteCarloConfig(num_paths=150, seed=99, return_volatility=0.0),
    )
    volatile = run_monte_carlo(
        p,
        s,
        MonteCarloConfig(num_paths=150, seed=99, return_volatility=0.25),
    )
    assert volatile.success_rate <= stable.success_rate
