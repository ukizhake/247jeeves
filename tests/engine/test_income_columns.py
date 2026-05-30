import json
from pathlib import Path

import pytest

from engine.models.profile import Profile, ScenarioOverrides
from engine.simulator import simulate

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_consulting_stops_at_age_70():
    data = json.loads((FIXTURES / "tech_fire_couple.json").read_text())
    data["age"] = 65
    data["plan_to_age"] = 72
    data["income"] = {
        "rental": 0,
        "dividends": 0,
        "pension": 0,
        "consulting": 50_000,
    }
    profile = Profile.model_validate(data)
    result = simulate(profile, ScenarioOverrides(horizon_years=8, roth_conversion_annual=0))

    assert result.years[0].age == 65
    assert result.years[0].consulting_income == 50_000
    assert result.years[4].age == 69
    assert result.years[4].consulting_income == pytest.approx(50_000 * (1.03**4), rel=1e-4)
    assert result.years[5].age == 70
    assert result.years[5].consulting_income == 0


def test_rental_and_fund_income_in_year_state():
    data = json.loads((FIXTURES / "tech_fire_couple.json").read_text())
    data["income"] = {
        "rental": 24_000,
        "dividends": 18_000,
        "pension": 0,
        "consulting": 0,
    }
    profile = Profile.model_validate(data)
    result = simulate(profile, ScenarioOverrides(horizon_years=3, roth_conversion_annual=0))

    y0 = result.years[0]
    assert y0.rental_income == 24_000
    assert y0.fund_income == 18_000
    assert y0.total_income > y0.rental_income + y0.fund_income
