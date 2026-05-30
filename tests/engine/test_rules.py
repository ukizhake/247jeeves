"""Rules engine smoke tests against Richer Retirement YAML rules."""

import json
from pathlib import Path

from engine.models.profile import Profile, ScenarioOverrides
from engine.rules.runner import _load_rules, run_rules
from engine.simulator import simulate

FIXTURE = Path(__file__).parent.parent / "fixtures" / "tech_fire_couple.json"


def test_rules_load():
    rules = _load_rules()
    assert len(rules) >= 40
    names = {r["rule_name"] for r in rules}
    assert "income_layering" in names
    assert "goldilocks_ptc" in names
    assert "sepp_72t_plan" in names
    assert "caution_rmd_roth_conversion" in names


def test_rules_fire_couple_early_retirement():
    data = json.loads(FIXTURE.read_text())
    profile = Profile(**data)
    scenario = ScenarioOverrides(name="Base")
    result = simulate(profile, scenario)
    recs = run_rules(profile, scenario, result)

    assert len(recs) > 0
    rule_ids = {r.rule_id for r in recs}
    assert "income_layering" in rule_ids or "sequence_returns_taxable_first" in rule_ids
    assert all(r.title for r in recs)
    assert all(r.actions for r in recs)


def test_new_conditions_spouse_older():
    data = json.loads(FIXTURE.read_text())
    profile = Profile(**data)
    assert profile.spouse_age is not None
    assert profile.spouse_age > profile.age  # spouse is older in fixture

    scenario = ScenarioOverrides(name="Base")
    result = simulate(profile, scenario)
    recs = run_rules(profile, scenario, result)
    # older_spouse_ira_first requires pre_rmd phase — not active at age 58
    assert "older_spouse_ira_first" not in {r.rule_id for r in recs}
