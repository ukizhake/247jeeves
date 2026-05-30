from engine.models.profile import Profile, ScenarioOverrides
from engine.simulator import simulate


def test_social_security_applies_cola_after_claim():
    profile = Profile.model_validate(
        {
            "name": "SS COLA",
            "age": 68,
            "plan_to_age": 72,
            "filing_status": "single",
            "annual_spending": 50_000,
            "social_security_claim_age": 70,
            "social_security_annual_at_claim": 48_000,
            "social_security_cola_rate": 0.02,
            "accounts": {"traditional_ira": 0, "roth_ira": 0, "taxable": 500_000, "cash": 0},
        }
    )
    result = simulate(profile, ScenarioOverrides(horizon_years=5, roth_conversion_annual=0))
    assert result.years[0].social_security == 0
    assert result.years[2].age == 70
    assert result.years[2].social_security == 48_000
    assert result.years[4].age == 72
    assert result.years[4].social_security == 48_000 * (1.02**2)


def test_household_ss_includes_spouse_mfj():
    profile = Profile.model_validate(
        {
            "name": "Couple",
            "age": 70,
            "spouse_age": 70,
            "plan_to_age": 71,
            "filing_status": "mfj",
            "annual_spending": 80_000,
            "social_security_claim_age": 70,
            "social_security_annual_at_claim": 48_000,
            "spouse_social_security_annual_at_claim": 24_000,
            "accounts": {"traditional_ira": 0, "roth_ira": 0, "taxable": 400_000, "cash": 0},
        }
    )
    result = simulate(profile, ScenarioOverrides(horizon_years=2, roth_conversion_annual=0))
    assert result.years[0].social_security == 72_000
