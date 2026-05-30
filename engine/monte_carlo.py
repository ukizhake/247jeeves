"""Monte Carlo simulation — random return paths through the deterministic engine."""

from __future__ import annotations

import random
from dataclasses import dataclass

from engine.models.profile import Profile, ScenarioOverrides
from engine.models.simulation import MonteCarloResult, MonteCarloYearBand
from engine.simulator import projection_horizon_years, simulate


def _percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * pct
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def _total_wealth(result) -> float:
    last = result.years[-1]
    return last.traditional_ira + last.roth_ira + last.taxable + last.cash


def _plan_succeeded(result) -> bool:
    return all(y.unfunded_spending < 1.0 for y in result.years)


def sample_annual_returns(
    mean: float,
    volatility: float,
    horizon: int,
    rng: random.Random,
) -> list[float]:
    """Independent annual returns; clipped to avoid absurd paths."""
    rates: list[float] = []
    for _ in range(horizon):
        r = rng.gauss(mean, volatility)
        rates.append(max(-0.5, min(0.5, r)))
    return rates


@dataclass
class MonteCarloConfig:
    num_paths: int = 500
    seed: int | None = None
    mean_return: float | None = None
    return_volatility: float | None = None


def run_monte_carlo(
    profile: Profile,
    scenario: ScenarioOverrides | None = None,
    config: MonteCarloConfig | None = None,
) -> MonteCarloResult:
    scenario = scenario or ScenarioOverrides()
    config = config or MonteCarloConfig()
    horizon = projection_horizon_years(profile, scenario)
    mean = config.mean_return if config.mean_return is not None else profile.return_rate
    vol = (
        config.return_volatility
        if config.return_volatility is not None
        else profile.return_volatility
    )

    rng = random.Random(config.seed)
    mc_scenario = scenario.model_copy(update={"return_scenario": "base", "name": "Monte Carlo"})

    wealth_by_year: list[list[float]] = [[] for _ in range(horizon)]
    final_wealths: list[float] = []
    successes = 0

    for _ in range(config.num_paths):
        rates = sample_annual_returns(mean, vol, horizon, rng)
        result = simulate(
            profile,
            mc_scenario,
            return_rates=rates,
            run_recommendations=False,
        )
        if _plan_succeeded(result):
            successes += 1
        final_wealths.append(_total_wealth(result))
        for i, year in enumerate(result.years):
            wealth_by_year[i].append(
                year.traditional_ira + year.roth_ira + year.taxable + year.cash
            )

    final_sorted = sorted(final_wealths)
    year_bands: list[MonteCarloYearBand] = []
    for i in range(horizon):
        vals = sorted(wealth_by_year[i])
        year_bands.append(
            MonteCarloYearBand(
                year=profile.projection_start_year + i,
                age=profile.age + i,
                p10=round(_percentile(vals, 0.10), 2),
                p50=round(_percentile(vals, 0.50), 2),
                p90=round(_percentile(vals, 0.90), 2),
            )
        )

    return MonteCarloResult(
        num_paths=config.num_paths,
        success_rate=round(successes / config.num_paths, 4) if config.num_paths else 0.0,
        median_final_wealth=round(_percentile(final_sorted, 0.50), 2),
        p10_final_wealth=round(_percentile(final_sorted, 0.10), 2),
        p90_final_wealth=round(_percentile(final_sorted, 0.90), 2),
        mean_return=mean,
        return_volatility=vol,
        year_bands=year_bands,
        meta={
            "horizon_years": horizon,
            "seed": config.seed,
            "net_portfolio_income": scenario.net_portfolio_income,
        },
    )
