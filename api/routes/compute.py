from fastapi import APIRouter

from api.schemas import (
    AnnualReviewComputeRequest,
    AnnualReviewComputeResponse,
    AnnuityComparisonComputeResponse,
    MonteCarloComputeRequest,
    MonteCarloComputeResponse,
    ProfileComputeBody,
    RebalanceComputeResponse,
    SafemaxComputeRequest,
    SafemaxComputeResponse,
    SimulateComputeRequest,
    SimulateComputeResponse,
    SpendingSchemeComparisonComputeResponse,
    StrategyComparisonComputeResponse,
)
from api.services import compute as compute_service

router = APIRouter(prefix="/compute", tags=["compute"])


@router.post("/simulate", response_model=SimulateComputeResponse)
def compute_simulate(body: SimulateComputeRequest) -> SimulateComputeResponse:
    result = compute_service.run_simulation(body.profile, body.scenario)
    return SimulateComputeResponse(result=result)


@router.post("/monte-carlo", response_model=MonteCarloComputeResponse)
def compute_monte_carlo(body: MonteCarloComputeRequest) -> MonteCarloComputeResponse:
    result = compute_service.run_monte_carlo_simulation(
        body.profile,
        body.scenario,
        num_paths=body.num_paths,
        seed=body.seed,
    )
    return MonteCarloComputeResponse(result=result)


@router.post("/rebalance-report", response_model=RebalanceComputeResponse)
def compute_rebalance_report(body: ProfileComputeBody) -> RebalanceComputeResponse:
    result = compute_service.run_rebalance_report(body.profile)
    return RebalanceComputeResponse(result=result)


@router.post("/annual-review", response_model=AnnualReviewComputeResponse)
def compute_annual_review(body: AnnualReviewComputeRequest) -> AnnualReviewComputeResponse:
    result = compute_service.run_annual_review(
        body.profile,
        prior_year_return=body.prior_year_return,
    )
    return AnnualReviewComputeResponse(result=result)


@router.post("/annuity-compare", response_model=AnnuityComparisonComputeResponse)
def compute_annuity_compare(body: MonteCarloComputeRequest) -> AnnuityComparisonComputeResponse:
    result = compute_service.run_annuity_comparison(
        body.profile,
        body.scenario,
        num_paths=body.num_paths,
        seed=body.seed,
    )
    return AnnuityComparisonComputeResponse(result=result)


@router.post("/safemax-report", response_model=SafemaxComputeResponse)
def compute_safemax_report(body: SafemaxComputeRequest) -> SafemaxComputeResponse:
    result = compute_service.run_safemax_report(
        body.profile,
        run_mc_validation=body.run_mc_validation,
        num_paths=body.num_paths,
    )
    return SafemaxComputeResponse(result=result)


@router.post("/spending-compare", response_model=SpendingSchemeComparisonComputeResponse)
def compute_spending_compare(
    body: MonteCarloComputeRequest,
) -> SpendingSchemeComparisonComputeResponse:
    result = compute_service.run_spending_scheme_comparison(
        body.profile,
        body.scenario,
        num_paths=body.num_paths,
        seed=body.seed,
    )
    return SpendingSchemeComparisonComputeResponse(result=result)


@router.post("/strategy-compare", response_model=StrategyComparisonComputeResponse)
def compute_strategy_compare(
    body: MonteCarloComputeRequest,
) -> StrategyComparisonComputeResponse:
    result = compute_service.run_strategy_comparison(
        body.profile,
        body.scenario,
        num_paths=body.num_paths,
        seed=body.seed,
    )
    return StrategyComparisonComputeResponse(result=result)
