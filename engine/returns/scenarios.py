"""Deterministic return paths for stress testing (Phase 2a)."""

from __future__ import annotations

from enum import Enum

from engine.models.profile import Profile, ScenarioOverrides


class ReturnScenario(str, Enum):
    BASE = "base"
    BAD_EARLY = "bad_early"
    FLAT_LOW = "flat_low"


# Year-indexed overrides; after the schedule ends, profile.return_rate applies.
RETURN_SCHEDULES: dict[ReturnScenario, list[float] | None] = {
    ReturnScenario.BASE: None,
    ReturnScenario.BAD_EARLY: [-0.15, -0.10, -0.05, 0.0, 0.05, 0.05, 0.06, 0.06, 0.06, 0.06],
    ReturnScenario.FLAT_LOW: [0.02] * 10,
}


RETURN_SCENARIO_LABELS: dict[ReturnScenario, str] = {
    ReturnScenario.BASE: "Base (profile return rate every year)",
    ReturnScenario.BAD_EARLY: "Bad early decade (−15%, −10%, −5%, then recovery)",
    ReturnScenario.FLAT_LOW: "Flat / low (2% for 10 years, then base)",
}


def resolve_return_rate(
    profile: Profile,
    scenario: ScenarioOverrides,
    year_index: int,
) -> float:
    """Return rate for a projection year (decimal, e.g. 0.06 = 6%)."""
    base = profile.return_rate
    try:
        key = ReturnScenario(scenario.return_scenario)
    except ValueError:
        key = ReturnScenario.BASE
    schedule = RETURN_SCHEDULES.get(key)
    if schedule is None or year_index >= len(schedule):
        return base
    return schedule[year_index]
