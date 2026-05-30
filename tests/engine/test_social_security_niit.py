from engine.calculations.niit import compute_niit
from engine.calculations.social_security import taxable_social_security
from engine.calculations.tax import compute_federal_tax_stacked
from engine.models.profile import FilingStatus, Profile


def test_ss_zero_below_tier1_mfj():
    # combined = 10k + 15k = 25k < 32k
    assert taxable_social_security(30_000, 10_000, FilingStatus.MFJ) == 0


def test_ss_fifty_percent_tier_mfj():
    # combined = 29k + 15k = 44k (top of 50% tier)
    taxable = taxable_social_security(30_000, 29_000, FilingStatus.MFJ)
    assert taxable == min(15_000, 0.5 * (44_000 - 32_000))


def test_ss_eighty_five_percent_widow_example():
    """Richer Retirement slide 31 — ~85% of SS taxable when income is high."""
    ss_gross = 36_000
    other = 114_000
    taxable = taxable_social_security(ss_gross, other, FilingStatus.MFJ)
    assert taxable == 30_600


def test_niit_above_threshold_mfj():
    # MAGI 300k, NII 80k, threshold 250k → 3.8% × 50k
    assert compute_niit(300_000, 80_000, FilingStatus.MFJ) == 1_900


def test_niit_below_threshold():
    assert compute_niit(200_000, 50_000, FilingStatus.MFJ) == 0


def test_integrated_tax_includes_niit():
    profile = Profile(
        name="High MAGI",
        age=60,
        filing_status=FilingStatus.MFJ,
        annual_spending=100_000,
        income={"dividends": 40_000, "rental": 0, "qualified_dividend_ratio": 0.5},
        accounts={"traditional_ira": 0, "roth_ira": 0, "taxable": 0, "cash": 0},
    )
    result = compute_federal_tax_stacked(
        200_000,
        100_000,
        profile,
        60,
        net_investment_income=140_000,
    )
    assert result.niit_tax > 0
    assert result.federal_tax == result.income_tax + result.niit_tax
