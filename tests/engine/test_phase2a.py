"""Phase 2a: net spending, return scenarios."""

from engine.models.profile import FilingStatus, Profile, ScenarioOverrides
from engine.simulator import simulate


def test_net_portfolio_income_reduces_withdrawals():
    p = Profile(
        name="net spend",
        age=58,
        filing_status=FilingStatus.MFJ,
        accounts={
            "traditional_ira": 500_000,
            "roth_ira": 50_000,
            "taxable": 1_000_000,
            "cash": 50_000,
        },
        income={"rental": 0, "dividends": 40_000},
        annual_spending=120_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        return_rate=0.06,
        inflation_rate=0.03,
    )
    net_on = simulate(
        p,
        ScenarioOverrides(horizon_years=1, roth_conversion_annual=0, net_portfolio_income=True),
    )
    net_off = simulate(
        p,
        ScenarioOverrides(horizon_years=1, roth_conversion_annual=0, net_portfolio_income=False),
    )
    y_on = net_on.years[0]
    y_off = net_off.years[0]

    assert y_on.portfolio_income == 40_000
    assert y_on.spending_target == 120_000
    assert y_on.withdrawal_need == 80_000
    assert y_on.withdrawal_taxable == 80_000
    assert y_off.withdrawal_taxable == 120_000


def test_bad_early_return_scenario_year_one():
    p = Profile(
        name="stress",
        age=58,
        filing_status=FilingStatus.SINGLE,
        accounts={"traditional_ira": 1_000_000, "roth_ira": 0, "taxable": 500_000, "cash": 0},
        income={"dividends": 0, "rental": 0},
        annual_spending=50_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        return_rate=0.06,
        inflation_rate=0.03,
    )
    result = simulate(
        p,
        ScenarioOverrides(
            horizon_years=2,
            roth_conversion_annual=0,
            return_scenario="bad_early",
            net_portfolio_income=True,
        ),
    )
    assert result.years[0].return_rate_applied == -0.15
    assert result.years[0].traditional_ira == 850_000
    assert result.years[1].return_rate_applied == -0.10
    assert result.meta["return_scenario"] == "bad_early"
