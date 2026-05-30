"""Staggered Social Security when spouses have different ages and claim ages."""

import pytest

from engine.models.profile import Profile, ScenarioOverrides
from engine.simulator import simulate


def test_spouse_ss_starts_before_primary_when_older():
    """Primary 58, spouse 62 in 2026 — both claim at 70; spouse SS starts 4 years earlier."""
    profile = Profile.model_validate(
        {
            "name": "Couple staggered",
            "age": 58,
            "spouse_age": 62,
            "plan_to_age": 72,
            "projection_start_year": 2026,
            "filing_status": "mfj",
            "annual_spending": 100_000,
            "social_security_claim_age": 70,
            "spouse_social_security_claim_age": 70,
            "social_security_annual_at_claim": 48_000,
            "spouse_social_security_annual_at_claim": 36_000,
            "accounts": {"traditional_ira": 0, "roth_ira": 0, "taxable": 800_000, "cash": 0},
        }
    )
    result = simulate(profile, ScenarioOverrides(roth_conversion_annual=0))

    y2026 = result.years[0]
    assert y2026.year == 2026
    assert y2026.age == 58
    assert y2026.spouse_age == 62
    assert y2026.primary_social_security == 0
    assert y2026.spouse_social_security == 0

    # 2034: spouse turns 70, primary is 66
    y2034 = next(y for y in result.years if y.year == 2034)
    assert y2034.age == 66
    assert y2034.spouse_age == 70
    assert y2034.primary_social_security == 0
    assert y2034.spouse_social_security == 36_000
    assert y2034.social_security == 36_000

    # 2038: primary turns 70, spouse is 74
    y2038 = next(y for y in result.years if y.year == 2038)
    assert y2038.age == 70
    assert y2038.spouse_age == 74
    assert y2038.primary_social_security == 48_000
    assert y2038.spouse_social_security == pytest.approx(36_000 * (1.03**4), rel=1e-4)
    assert y2038.social_security == pytest.approx(
        48_000 + 36_000 * (1.03**4), rel=1e-4
    )


def test_different_claim_ages_same_calendar_year():
    """Spouse can claim at 62 while primary waits until 70."""
    profile = Profile.model_validate(
        {
            "name": "Different claims",
            "age": 58,
            "spouse_age": 62,
            "plan_to_age": 65,
            "projection_start_year": 2026,
            "filing_status": "mfj",
            "annual_spending": 80_000,
            "social_security_claim_age": 70,
            "spouse_social_security_claim_age": 62,
            "social_security_annual_at_claim": 48_000,
            "spouse_social_security_annual_at_claim": 24_000,
            "accounts": {"traditional_ira": 0, "roth_ira": 0, "taxable": 500_000, "cash": 0},
        }
    )
    result = simulate(profile, ScenarioOverrides(horizon_years=8, roth_conversion_annual=0))

    y2026 = result.years[0]
    assert y2026.spouse_social_security == 24_000
    assert y2026.primary_social_security == 0

    y2033 = next(y for y in result.years if y.year == 2033)
    assert y2033.age == 65
    assert y2033.spouse_age == 69
    assert y2033.primary_social_security == 0
    assert y2033.spouse_social_security == pytest.approx(24_000 * (1.03**7), rel=1e-4)
