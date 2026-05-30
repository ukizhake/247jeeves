import json
from pathlib import Path

from engine.models.profile import Profile, ScenarioOverrides
from engine.simulator import simulate

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_tech_fire_couple_runs_and_has_recommendations():
    data = json.loads((FIXTURES / "tech_fire_couple.json").read_text())
    profile = Profile.model_validate(data)
    result = simulate(profile, ScenarioOverrides(horizon_years=25))

    assert len(result.years) == 25
    assert result.years[0].phase == "early_retirement"
    assert result.summary.lifetime_federal_tax > 0
    assert len(result.recommendations) >= 1


def test_rmd_appears_at_75():
    data = json.loads((FIXTURES / "tech_fire_couple.json").read_text())
    profile = Profile.model_validate(data)
    # No conversions + moderate spending so IRA remains at RMD age
    result = simulate(
        profile,
        ScenarioOverrides(horizon_years=30, roth_conversion_annual=0, spending_override=80_000),
    )

    age_75 = next(y for y in result.years if y.age == 75)
    assert age_75.phase == "rmd_years"
    assert age_75.traditional_ira > 0
    assert age_75.rmd_required > 0
    assert result.summary.rmd_at_age_75 == age_75.rmd_required


def test_roth_conversion_scenario():
    data = json.loads((FIXTURES / "tech_fire_couple.json").read_text())
    profile = Profile.model_validate(data)
    base = simulate(profile, ScenarioOverrides(horizon_years=10, roth_conversion_annual=0))
    aggressive = simulate(
        profile,
        ScenarioOverrides(horizon_years=10, roth_conversion_annual=80_000),
    )
    base_ira = base.years[-1].traditional_ira
    agg_ira = aggressive.years[-1].traditional_ira
    assert agg_ira < base_ira
