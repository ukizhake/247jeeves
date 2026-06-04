"""Phase 3a: annual spending review endpoint logic."""

from engine.annual_review import compute_annual_review
from engine.models.profile import FilingStatus, Profile


def test_annual_review_recommends_cola_after_up_year():
    p = Profile(
        name="review",
        age=65,
        filing_status=FilingStatus.SINGLE,
        accounts={"traditional_ira": 2_000_000, "roth_ira": 0, "taxable": 0, "cash": 0},
        income={"dividends": 10_000, "rental": 0},
        annual_spending=80_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        return_rate=0.06,
        inflation_rate=0.03,
        withdrawal_scheme="performance_cola",
        annuity_income_annual=20_000,
        annual_review_month=10,
    )
    result = compute_annual_review(p, prior_year_return=0.07)
    assert result.review_month == 10
    assert result.review_month_name == "October"
    assert result.recommended_annual_spending == 82_400
    assert result.annuity_income == 20_000
    assert result.cola_dollar_change == 2_400
    assert result.withdrawal_scheme == "performance_cola"
    assert any("Annuity" in s for s in result.suggestions)


def test_annual_review_holds_spending_after_down_year():
    p = Profile(
        name="hold",
        age=65,
        filing_status=FilingStatus.SINGLE,
        accounts={"traditional_ira": 1_000_000, "roth_ira": 0, "taxable": 0, "cash": 0},
        income={"dividends": 0, "rental": 0},
        annual_spending=100_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        return_rate=0.06,
        inflation_rate=0.03,
        withdrawal_scheme="performance_cola",
        performance_skip_cola_after_down_year=True,
    )
    result = compute_annual_review(p, prior_year_return=-0.15)
    assert result.recommended_annual_spending == 100_000
    assert "held flat" in result.performance_note
