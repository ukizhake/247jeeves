from engine import simulate
from engine.allocation.rebalance import compute_rebalance_report
from engine.annual_review import compute_annual_review
from engine.monte_carlo import (
    MonteCarloConfig,
    run_annuity_comparison as mc_annuity_comparison,
    run_monte_carlo,
    run_spending_scheme_comparison as mc_spending_scheme_comparison,
    run_strategy_comparison as mc_strategy_comparison,
)
from engine.models.profile import Profile, ScenarioOverrides
from engine.models.simulation import (
    AnnuityComparisonResult,
    MonteCarloResult,
    SimulationResult,
    SpendingSchemeComparisonResult,
    StrategyComparisonResult,
)
from engine.withdrawals.safemax import SafemaxReport, compute_safemax_report


def run_simulation(
    profile: Profile, scenario: ScenarioOverrides | None = None
) -> SimulationResult:
    scenario = scenario or ScenarioOverrides()
    return simulate(profile, scenario)


def run_monte_carlo_simulation(
    profile: Profile,
    scenario: ScenarioOverrides | None = None,
    *,
    num_paths: int = 500,
    seed: int | None = None,
) -> MonteCarloResult:
    scenario = scenario or ScenarioOverrides()
    config = MonteCarloConfig(num_paths=num_paths, seed=seed)
    return run_monte_carlo(profile, scenario, config)


def run_rebalance_report(profile: Profile):
    return compute_rebalance_report(profile)


def run_annual_review(profile: Profile, *, prior_year_return: float | None = None):
    return compute_annual_review(profile, prior_year_return=prior_year_return)


def run_annuity_comparison(
    profile: Profile,
    scenario: ScenarioOverrides | None = None,
    *,
    num_paths: int = 500,
    seed: int | None = None,
) -> AnnuityComparisonResult:
    scenario = scenario or ScenarioOverrides()
    config = MonteCarloConfig(num_paths=num_paths, seed=seed)
    return mc_annuity_comparison(profile, scenario, config)


def run_safemax_report(
    profile: Profile,
    *,
    run_mc_validation: bool = True,
    num_paths: int = 200,
) -> SafemaxReport:
    return compute_safemax_report(
        profile,
        run_mc_validation=run_mc_validation,
        mc_paths=num_paths,
    )


def run_spending_scheme_comparison(
    profile: Profile,
    scenario: ScenarioOverrides | None = None,
    *,
    num_paths: int = 500,
    seed: int | None = None,
) -> SpendingSchemeComparisonResult:
    scenario = scenario or ScenarioOverrides()
    config = MonteCarloConfig(num_paths=num_paths, seed=seed)
    return mc_spending_scheme_comparison(profile, scenario, config)


def run_strategy_comparison(
    profile: Profile,
    scenario: ScenarioOverrides | None = None,
    *,
    num_paths: int = 500,
    seed: int | None = None,
) -> StrategyComparisonResult:
    scenario = scenario or ScenarioOverrides()
    config = MonteCarloConfig(num_paths=num_paths, seed=seed)
    return mc_strategy_comparison(profile, scenario, config)
