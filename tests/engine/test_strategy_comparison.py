"""Phase 2c: withdrawal strategy comparison on shared Monte Carlo paths."""

from engine.monte_carlo import MonteCarloConfig, run_strategy_comparison
from engine.models.profile import FilingStatus, Profile, ScenarioOverrides
from engine.simulator import simulate
from engine.withdrawals.policy import WithdrawalPolicy


def _wealthy_profile(**kwargs) -> Profile:
    defaults = dict(
        name="strategy",
        age=58,
        plan_to_age=85,
        filing_status=FilingStatus.MFJ,
        accounts={
            "traditional_ira": 1_500_000,
            "roth_ira": 200_000,
            "taxable": 2_000_000,
            "cash": 150_000,
        },
        income={"dividends": 40_000, "rental": 0},
        annual_spending=120_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        return_rate=0.06,
        return_volatility=0.18,
        inflation_rate=0.03,
    )
    defaults.update(kwargs)
    return Profile(**defaults)


def test_strategy_comparison_four_policies():
    p = _wealthy_profile()
    result = run_strategy_comparison(
        p,
        ScenarioOverrides(horizon_years=12, roth_conversion_annual=0),
        MonteCarloConfig(num_paths=80, seed=7),
    )
    assert len(result.strategies) == 4
    policies = {s.policy for s in result.strategies}
    assert policies == {
        WithdrawalPolicy.PHASE_DEFAULT.value,
        WithdrawalPolicy.TAXABLE_FIRST.value,
        WithdrawalPolicy.CASH_FIRST.value,
        WithdrawalPolicy.IRA_FIRST.value,
    }


def test_strategy_comparison_reproducible_with_seed():
    p = _wealthy_profile()
    s = ScenarioOverrides(horizon_years=10, roth_conversion_annual=0)
    cfg = MonteCarloConfig(num_paths=50, seed=123)
    a = run_strategy_comparison(p, s, cfg)
    b = run_strategy_comparison(p, s, cfg)
    assert a.strategies[0].success_rate == b.strategies[0].success_rate
    assert a.strategies[0].median_final_wealth == b.strategies[0].median_final_wealth


def test_cash_first_differs_from_phase_default_on_shared_returns():
    p = _wealthy_profile()
    rates = [[0.06] * 5]
    s_default = ScenarioOverrides(
        horizon_years=5,
        roth_conversion_annual=0,
        withdrawal_policy="phase_default",
    )
    s_cash = s_default.model_copy(update={"withdrawal_policy": "cash_first"})
    default = simulate(p, s_default, return_rates=rates[0], run_recommendations=False)
    cash = simulate(p, s_cash, return_rates=rates[0], run_recommendations=False)
    assert default.years[0].cash != cash.years[0].cash or default.summary.final_total_wealth != cash.summary.final_total_wealth
