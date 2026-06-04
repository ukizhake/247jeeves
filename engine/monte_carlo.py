"""Monte Carlo simulation — random return paths through the deterministic engine."""

from __future__ import annotations

import random
from dataclasses import dataclass

from engine.models.profile import Profile, ScenarioOverrides
from engine.models.simulation import (
    MonteCarloResult,
    MonteCarloYearBand,
    SpendingSchemeComparisonResult,
    SpendingSchemeSummary,
    StrategyComparisonResult,
    StrategySummary,
)
from engine.simulator import projection_horizon_years, simulate
from engine.withdrawals.policy import POLICY_LABELS, WithdrawalPolicy
from engine.withdrawals.spending import COMPARISON_SCHEMES, SCHEME_LABELS, WithdrawalScheme


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


def generate_return_paths(
    mean: float,
    volatility: float,
    horizon: int,
    num_paths: int,
    seed: int | None,
) -> list[list[float]]:
    rng = random.Random(seed)
    return [sample_annual_returns(mean, volatility, horizon, rng) for _ in range(num_paths)]


@dataclass
class MonteCarloConfig:
    num_paths: int = 500
    seed: int | None = None
    mean_return: float | None = None
    return_volatility: float | None = None


COMPARISON_POLICIES: tuple[WithdrawalPolicy, ...] = (
    WithdrawalPolicy.PHASE_DEFAULT,
    WithdrawalPolicy.TAXABLE_FIRST,
    WithdrawalPolicy.CASH_FIRST,
    WithdrawalPolicy.IRA_FIRST,
)


def run_monte_carlo(
    profile: Profile,
    scenario: ScenarioOverrides | None = None,
    config: MonteCarloConfig | None = None,
    *,
    return_paths: list[list[float]] | None = None,
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

    if return_paths is None:
        return_paths = generate_return_paths(mean, vol, horizon, config.num_paths, config.seed)

    mc_scenario = scenario.model_copy(update={"return_scenario": "base", "name": "Monte Carlo"})
    final_wealths: list[float] = []
    wealth_by_year: list[list[float]] = [[] for _ in range(horizon)]
    successes = 0

    for rates in return_paths:
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

    num_paths = len(return_paths)
    return MonteCarloResult(
        num_paths=num_paths,
        success_rate=round(successes / num_paths, 4) if num_paths else 0.0,
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
            "withdrawal_policy": scenario.withdrawal_policy,
            "withdrawal_scheme": profile.withdrawal_scheme,
        },
    )


def _lifetime_spending(result) -> float:
    return sum(y.spending_target for y in result.years)


def run_spending_scheme_comparison(
    profile: Profile,
    scenario: ScenarioOverrides | None = None,
    config: MonteCarloConfig | None = None,
    *,
    schemes: tuple[WithdrawalScheme, ...] | None = None,
) -> SpendingSchemeComparisonResult:
    """Compare COLA / FA / performance / FP spending on shared Monte Carlo paths (Phase 3c)."""
    scenario = scenario or ScenarioOverrides()
    config = config or MonteCarloConfig()
    compare_schemes = schemes or COMPARISON_SCHEMES
    horizon = projection_horizon_years(profile, scenario)
    mean = config.mean_return if config.mean_return is not None else profile.return_rate
    vol = (
        config.return_volatility
        if config.return_volatility is not None
        else profile.return_volatility
    )

    return_paths = generate_return_paths(mean, vol, horizon, config.num_paths, config.seed)
    summaries: list[SpendingSchemeSummary] = []

    for scheme in compare_schemes:
        mc_scenario = scenario.model_copy(
            update={
                "return_scenario": "base",
                "name": f"Spending {scheme.value}",
                "spending_scheme_override": scheme.value,
            }
        )
        final_wealths: list[float] = []
        lifetime_spending: list[float] = []
        lifetime_taxes: list[float] = []
        successes = 0

        for rates in return_paths:
            result = simulate(
                profile,
                mc_scenario,
                return_rates=rates,
                run_recommendations=False,
            )
            if _plan_succeeded(result):
                successes += 1
            final_wealths.append(_total_wealth(result))
            lifetime_spending.append(_lifetime_spending(result))
            lifetime_taxes.append(result.summary.lifetime_federal_tax)

        wealth_sorted = sorted(final_wealths)
        spend_sorted = sorted(lifetime_spending)
        tax_sorted = sorted(lifetime_taxes)
        summaries.append(
            SpendingSchemeSummary(
                scheme=scheme.value,
                label=SCHEME_LABELS[scheme],
                success_rate=round(successes / config.num_paths, 4) if config.num_paths else 0.0,
                median_final_wealth=round(_percentile(wealth_sorted, 0.50), 2),
                p10_final_wealth=round(_percentile(wealth_sorted, 0.10), 2),
                p90_final_wealth=round(_percentile(wealth_sorted, 0.90), 2),
                median_lifetime_spending=round(_percentile(spend_sorted, 0.50), 2),
                median_lifetime_tax=round(_percentile(tax_sorted, 0.50), 2),
            )
        )

    return SpendingSchemeComparisonResult(
        num_paths=config.num_paths,
        seed=config.seed,
        mean_return=mean,
        return_volatility=vol,
        schemes=summaries,
        meta={
            "horizon_years": horizon,
            "net_portfolio_income": scenario.net_portfolio_income,
            "withdrawal_policy": scenario.withdrawal_policy,
        },
    )


def run_strategy_comparison(
    profile: Profile,
    scenario: ScenarioOverrides | None = None,
    config: MonteCarloConfig | None = None,
    *,
    policies: tuple[WithdrawalPolicy, ...] | None = None,
) -> StrategyComparisonResult:
    """Run multiple withdrawal policies on the same random return paths (Phase 2c)."""
    scenario = scenario or ScenarioOverrides()
    config = config or MonteCarloConfig()
    compare_policies = policies or COMPARISON_POLICIES
    horizon = projection_horizon_years(profile, scenario)
    mean = config.mean_return if config.mean_return is not None else profile.return_rate
    vol = (
        config.return_volatility
        if config.return_volatility is not None
        else profile.return_volatility
    )

    return_paths = generate_return_paths(mean, vol, horizon, config.num_paths, config.seed)
    strategies: list[StrategySummary] = []

    for policy in compare_policies:
        mc_scenario = scenario.model_copy(
            update={
                "return_scenario": "base",
                "name": f"Strategy {policy.value}",
                "withdrawal_policy": policy.value,
            }
        )
        final_wealths: list[float] = []
        lifetime_taxes: list[float] = []
        successes = 0

        for rates in return_paths:
            result = simulate(
                profile,
                mc_scenario,
                return_rates=rates,
                run_recommendations=False,
            )
            if _plan_succeeded(result):
                successes += 1
            final_wealths.append(_total_wealth(result))
            lifetime_taxes.append(result.summary.lifetime_federal_tax)

        final_sorted = sorted(final_wealths)
        tax_sorted = sorted(lifetime_taxes)
        strategies.append(
            StrategySummary(
                policy=policy.value,
                label=POLICY_LABELS[policy],
                success_rate=round(successes / config.num_paths, 4) if config.num_paths else 0.0,
                median_final_wealth=round(_percentile(final_sorted, 0.50), 2),
                p10_final_wealth=round(_percentile(final_sorted, 0.10), 2),
                p90_final_wealth=round(_percentile(final_sorted, 0.90), 2),
                median_lifetime_tax=round(_percentile(tax_sorted, 0.50), 2),
            )
        )

    return StrategyComparisonResult(
        num_paths=config.num_paths,
        seed=config.seed,
        mean_return=mean,
        return_volatility=vol,
        strategies=strategies,
        meta={
            "horizon_years": horizon,
            "net_portfolio_income": scenario.net_portfolio_income,
        },
    )
