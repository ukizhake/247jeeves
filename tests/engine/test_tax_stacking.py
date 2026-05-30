"""Tax stacking tests from Richer Retirement examples."""

from engine.calculations.tax import compute_federal_tax_stacked, total_deductions
from engine.models.profile import FilingStatus, Profile


def test_senior_deductions_mfj_both_67():
    profile = Profile(
        name="Eddie & Elizabeth",
        age=67,
        spouse_age=67,
        filing_status=FilingStatus.MFJ,
        annual_spending=100_000,
        accounts={"traditional_ira": 0, "roth_ira": 0, "taxable": 0, "cash": 0},
    )
    assert total_deductions(profile, 67) == 46_700  # 31500 + 3200 + 12000


def test_eddie_elizabeth_slide_12():
    """Slide 12: $50k IRA + $5k ordinary + $60k LTCG → $830 federal tax."""
    profile = Profile(
        name="Eddie & Elizabeth",
        age=67,
        spouse_age=67,
        filing_status=FilingStatus.MFJ,
        annual_spending=100_000,
        accounts={"traditional_ira": 0, "roth_ira": 0, "taxable": 0, "cash": 0},
    )
    result = compute_federal_tax_stacked(
        ordinary_income=55_000,
        long_term_capital_gains=60_000,
        profile=profile,
        age=67,
    )
    assert result.ordinary_taxable == 8_300
    assert result.ordinary_tax == 830
    assert result.ltcg_tax == 0
    assert result.federal_tax == 830
