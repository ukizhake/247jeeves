from engine.models.profile import Profile, ScenarioOverrides
from engine.simulator import projection_horizon_years, simulate
import json
from pathlib import Path

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_horizon_defaults_to_plan_to_age():
    data = json.loads((FIXTURES / "tech_fire_couple.json").read_text())
    profile = Profile.model_validate(data)
    assert projection_horizon_years(profile, ScenarioOverrides()) == 38  # 58..95 inclusive

    result = simulate(profile, ScenarioOverrides())
    assert result.years[-1].age == 95


def test_explicit_horizon_years_override():
    profile = Profile.model_validate(
        json.loads((FIXTURES / "tech_fire_couple.json").read_text())
    )
    assert projection_horizon_years(profile, ScenarioOverrides(horizon_years=10)) == 10
