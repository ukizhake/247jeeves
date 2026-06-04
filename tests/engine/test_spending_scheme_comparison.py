"""Phase 3c: spending scheme comparison on shared Monte Carlo paths."""

from engine.monte_carlo import MonteCarloConfig, run_spending_scheme_comparison
from engine.models.profile import FilingStatus, Profile, ScenarioOverrides
from engine.simulator import simulate
from engine.withdrawals.spending import WithdrawalScheme


def _profile(**kwargs) -> Profile:
    defaults = dict(
        name="spend cmp",
        age=62,
        plan_to_age=85,
        filing_status=FilingStatus.MFJ,
        accounts={
            "traditional_ira": 1_000_000,
            "roth_ira": 100_000,
            "taxable": 1_500_000,
            "cash": 100_000,
        },
        income={"dividends": 30_000, "rental": 0},
        annual_spending=120_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        return_rate=0.06,
        return_volatility=0.15,
        inflation_rate=0.03,
        initial_withdrawal_rate=0.05,
    )
    defaults.update(kwargs)
    return Profile(**defaults)


def test_spending_scheme_comparison_five_schemes():
    p = _profile()
    result = run_spending_scheme_comparison(
        p,
        ScenarioOverrides(horizon_years=10, roth_conversion_annual=0),
        MonteCarloConfig(num_paths=60, seed=11),
    )
    assert len(result.schemes) == 5
    schemes = {s.scheme for s in result.schemes}
    assert schemes == {
        WithdrawalScheme.COLA.value,
        WithdrawalScheme.FIXED_ANNUITY.value,
        WithdrawalScheme.PERFORMANCE_COLA.value,
        WithdrawalScheme.FIXED_PERCENTAGE.value,
        WithdrawalScheme.FLOOR_CEILING.value,
    }


def test_scenario_spending_scheme_override():
    p = _profile(withdrawal_scheme="cola")
    rates = [0.06] * 3
    cola = simulate(
        p,
        ScenarioOverrides(
            horizon_years=3,
            roth_conversion_annual=0,
            spending_scheme_override="fixed_annuity",
        ),
        return_rates=rates,
        run_recommendations=False,
    )
    assert cola.years[1].spending_target == cola.years[0].spending_target
    assert cola.meta["withdrawal_scheme"] == "fixed_annuity"
