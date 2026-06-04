"""Phase 3a: COLA, fixed annuity, performance-based spending."""

from engine.models.profile import FilingStatus, Profile
from engine.withdrawals.spending import (
    WithdrawalScheme,
    annuity_income_year,
    cola_rate,
    spending_for_year,
)


def _base_profile(**kwargs) -> Profile:
    defaults = dict(
        name="spend",
        age=65,
        filing_status=FilingStatus.SINGLE,
        accounts={"traditional_ira": 1_000_000, "roth_ira": 0, "taxable": 500_000, "cash": 0},
        income={"dividends": 0, "rental": 0},
        annual_spending=100_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        return_rate=0.06,
        inflation_rate=0.03,
    )
    defaults.update(kwargs)
    return Profile(**defaults)


def test_cola_rate_defaults_to_inflation():
    p = _base_profile()
    assert cola_rate(p) == 0.03
    p2 = _base_profile(spending_cola_rate=0.025)
    assert cola_rate(p2) == 0.025


def test_cola_increases_spending_year_two():
    p = _base_profile(withdrawal_scheme=WithdrawalScheme.COLA.value)
    y1, _ = spending_for_year(p, 1, base_annual=100_000, prior_spending=100_000, prior_year_return=0.05)
    assert y1 == 103_000


def test_fixed_annuity_nominal_flat():
    p = _base_profile(withdrawal_scheme=WithdrawalScheme.FIXED_ANNUITY.value)
    y1, note = spending_for_year(p, 1, base_annual=100_000, prior_spending=100_000, prior_year_return=-0.2)
    assert y1 == 100_000
    assert "unchanged" in note


def test_performance_cola_holds_after_down_year():
    p = _base_profile(
        withdrawal_scheme=WithdrawalScheme.PERFORMANCE_COLA.value,
        performance_skip_cola_after_down_year=True,
    )
    y1, note = spending_for_year(
        p, 1, base_annual=100_000, prior_spending=100_000, prior_year_return=-0.12
    )
    assert y1 == 100_000
    assert "held flat" in note


def test_performance_cola_raises_after_up_year():
    p = _base_profile(withdrawal_scheme=WithdrawalScheme.PERFORMANCE_COLA.value)
    y1, _ = spending_for_year(
        p, 1, base_annual=100_000, prior_spending=100_000, prior_year_return=0.08
    )
    assert y1 == 103_000


def test_performance_max_raise_cap():
    p = _base_profile(
        withdrawal_scheme=WithdrawalScheme.PERFORMANCE_COLA.value,
        spending_cola_rate=0.10,
        performance_max_raise_pct=0.05,
    )
    y1, note = spending_for_year(
        p, 1, base_annual=100_000, prior_spending=100_000, prior_year_return=0.2
    )
    assert y1 == 105_000
    assert "capped" in note


def test_annuity_income_with_cola():
    p = _base_profile(annuity_income_annual=24_000, annuity_cola_rate=0.02)
    assert annuity_income_year(p, 0) == 24_000
    assert annuity_income_year(p, 2) == 24_000 * (1.02**2)


def test_fixed_percentage_tracks_wealth():
    p = _base_profile(
        withdrawal_scheme=WithdrawalScheme.FIXED_PERCENTAGE.value,
        initial_withdrawal_rate=0.05,
    )
    amount, note = spending_for_year(
        p,
        2,
        base_annual=100_000,
        prior_spending=50_000,
        prior_year_return=0.1,
        wealth_start=2_000_000,
    )
    assert amount == 100_000
    assert "FP" in note


def test_simulator_annuity_reduces_withdrawal_need():
    from engine.models.profile import ScenarioOverrides
    from engine.simulator import simulate

    p = _base_profile(annuity_income_annual=30_000)
    result = simulate(
        p,
        ScenarioOverrides(horizon_years=1, roth_conversion_annual=0, net_portfolio_income=False),
    )
    y = result.years[0]
    assert y.annuity_income == 30_000
    assert y.withdrawal_need == 70_000
