"""Spouse / household modeling tests."""

from engine.calculations.tax import spouse_age_at, total_deductions
from engine.models.profile import FilingStatus, Profile


def test_spouse_age_advances_with_projection():
    profile = Profile(
        name="Couple",
        age=63,
        spouse_age=61,
        filing_status=FilingStatus.MFJ,
        annual_spending=80_000,
        accounts={"traditional_ira": 0, "roth_ira": 0, "taxable": 0, "cash": 0},
    )
    assert spouse_age_at(profile, 63) == 61
    assert spouse_age_at(profile, 65) == 63
    assert spouse_age_at(profile, 67) == 65


def test_senior_deductions_when_spouse_turns_65_later():
    profile = Profile(
        name="Couple staggered",
        age=65,
        spouse_age=63,
        filing_status=FilingStatus.MFJ,
        annual_spending=80_000,
        accounts={"traditional_ira": 0, "roth_ira": 0, "taxable": 0, "cash": 0},
    )
    # Primary 65, spouse 63 — one senior
    one_senior = total_deductions(profile, 65)
    # Primary 67, spouse 65 — both seniors
    both_senior = total_deductions(profile, 67)
    assert both_senior > one_senior


def test_single_has_no_spouse_deduction_boost():
    profile = Profile(
        name="Single",
        age=67,
        filing_status=FilingStatus.SINGLE,
        annual_spending=60_000,
        accounts={"traditional_ira": 0, "roth_ira": 0, "taxable": 0, "cash": 0},
    )
    single_ded = total_deductions(profile, 67)
    couple = Profile(
        name="Couple",
        age=67,
        spouse_age=67,
        filing_status=FilingStatus.MFJ,
        annual_spending=60_000,
        accounts={"traditional_ira": 0, "roth_ira": 0, "taxable": 0, "cash": 0},
    )
    couple_ded = total_deductions(couple, 67)
    assert couple_ded > single_ded
