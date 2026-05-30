"""Social Security benefit validation tests — no auto-correction."""

import pytest

from engine.models.profile import Profile, validate_social_security_annual


def test_valid_annual_unchanged():
    assert validate_social_security_annual(47_988) == 47_988


def test_five_thousand_monthly_becomes_sixty_thousand_annual():
    assert validate_social_security_annual(5_000 * 12) == 60_000


def test_rejects_corrupt_trailing_digit_value():
    with pytest.raises(ValueError, match="re-enter"):
        validate_social_security_annual(720_007, label="Spouse Social Security")


def test_rejects_annual_entered_in_monthly_field():
    with pytest.raises(ValueError, match="re-enter"):
        validate_social_security_annual(575_856)


def test_rejects_absurd_value():
    with pytest.raises(ValueError):
        validate_social_security_annual(5_000_000)


def test_profile_rejects_corrupt_spouse_on_load():
    with pytest.raises(ValueError):
        Profile.model_validate(
            {
                "name": "Couple",
                "age": 58,
                "filing_status": "mfj",
                "annual_spending": 120_000,
                "social_security_claim_age": 70,
                "social_security_annual_at_claim": 47_988,
                "spouse_social_security_annual_at_claim": 720_007,
                "accounts": {"traditional_ira": 0, "roth_ira": 0, "taxable": 0, "cash": 0},
            }
        )
