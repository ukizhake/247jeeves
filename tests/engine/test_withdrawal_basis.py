"""Taxable withdrawal splits basis (non-taxable) from gain (LTCG)."""

from engine.models.profile import FilingStatus, Profile
from engine.models.profile import ScenarioOverrides
from engine.simulator import simulate


def test_taxable_withdrawal_basis_not_in_ordinary_income():
    p = Profile(
        name="basis split",
        age=58,
        spouse_age=62,
        filing_status=FilingStatus.MFJ,
        accounts={
            "traditional_ira": 1_000_000,
            "roth_ira": 50_000,
            "taxable": 2_000_000,
            "cash": 50_000,
        },
        income={"rental": 96_000, "dividends": 40_000},
        annual_spending=180_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        taxable_cost_basis_ratio=0.8,
        return_rate=0.06,
        inflation_rate=0.03,
    )
    result = simulate(
        p,
        ScenarioOverrides(roth_conversion_annual=20_000, net_portfolio_income=False),
    )
    y = result.years[0]

    assert y.withdrawal_taxable == 180_000
    assert y.withdrawal_taxable_basis == 144_000
    assert y.withdrawal_taxable_gain == 36_000
    # Ordinary = rental + non-Q divs + Roth conv only (no basis)
    assert y.ordinary_income == 120_000
    assert y.long_term_capital_gains == 72_000
    assert y.agi == 192_000
    assert y.taxable_income == 160_500
