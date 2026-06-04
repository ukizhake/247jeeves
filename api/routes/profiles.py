from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models_db import ProfileRecord, ScenarioRecord
from api.schemas import (
    AnnualReviewRequest,
    AnnualReviewResponse,
    RebalanceReportResponse,
    MonteCarloRequest,
    MonteCarloResponse,
    ProfileCreate,
    ProfileResponse,
    ScenarioCreate,
    ScenarioResponse,
    SimulateRequest,
    SimulateResponse,
    StrategyComparisonResponse,
)
from engine import simulate
from engine.allocation.rebalance import compute_rebalance_report
from engine.annual_review import compute_annual_review
from engine.monte_carlo import MonteCarloConfig, run_monte_carlo, run_strategy_comparison
from engine.models.profile import Profile, ScenarioOverrides

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=ProfileResponse)
def create_profile(body: ProfileCreate, db: Session = Depends(get_db)) -> ProfileResponse:
    record = ProfileRecord(name=body.name, data_json=body.model_dump_json())
    db.add(record)
    db.commit()
    db.refresh(record)
    return ProfileResponse(id=record.id, profile=body)


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: int, db: Session = Depends(get_db)) -> ProfileResponse:
    record = db.get(ProfileRecord, profile_id)
    if not record:
        raise HTTPException(404, "Profile not found")
    profile = Profile.model_validate_json(record.data_json)
    return ProfileResponse(id=record.id, profile=profile)


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: int, body: ProfileCreate, db: Session = Depends(get_db)
) -> ProfileResponse:
    record = db.get(ProfileRecord, profile_id)
    if not record:
        raise HTTPException(404, "Profile not found")
    record.name = body.name
    record.data_json = body.model_dump_json()
    db.commit()
    db.refresh(record)
    return ProfileResponse(id=record.id, profile=body)


@router.post("/{profile_id}/scenarios", response_model=ScenarioResponse)
def create_scenario(
    profile_id: int, body: ScenarioCreate, db: Session = Depends(get_db)
) -> ScenarioResponse:
    if not db.get(ProfileRecord, profile_id):
        raise HTTPException(404, "Profile not found")
    overrides = body.overrides
    overrides.name = body.name
    record = ScenarioRecord(
        profile_id=profile_id,
        name=body.name,
        data_json=overrides.model_dump_json(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ScenarioResponse(
        id=record.id, profile_id=profile_id, name=record.name, overrides=overrides
    )


@router.post("/{profile_id}/simulate", response_model=SimulateResponse)
def simulate_profile(
    profile_id: int,
    body: SimulateRequest | None = None,
    db: Session = Depends(get_db),
) -> SimulateResponse:
    record = db.get(ProfileRecord, profile_id)
    if not record:
        raise HTTPException(404, "Profile not found")
    profile = Profile.model_validate_json(record.data_json)
    scenario = body.scenario if body and body.scenario else ScenarioOverrides()
    result = simulate(profile, scenario)
    return SimulateResponse(profile_id=profile_id, result=result)


@router.post("/{profile_id}/monte-carlo", response_model=MonteCarloResponse)
def monte_carlo_profile(
    profile_id: int,
    body: MonteCarloRequest | None = None,
    db: Session = Depends(get_db),
) -> MonteCarloResponse:
    record = db.get(ProfileRecord, profile_id)
    if not record:
        raise HTTPException(404, "Profile not found")
    profile = Profile.model_validate_json(record.data_json)
    body = body or MonteCarloRequest()
    scenario = body.scenario if body.scenario else ScenarioOverrides()
    config = MonteCarloConfig(num_paths=body.num_paths, seed=body.seed)
    result = run_monte_carlo(profile, scenario, config)
    return MonteCarloResponse(profile_id=profile_id, result=result)


@router.post("/{profile_id}/rebalance-report", response_model=RebalanceReportResponse)
def rebalance_report_profile(
    profile_id: int,
    db: Session = Depends(get_db),
) -> RebalanceReportResponse:
    record = db.get(ProfileRecord, profile_id)
    if not record:
        raise HTTPException(404, "Profile not found")
    profile = Profile.model_validate_json(record.data_json)
    result = compute_rebalance_report(profile)
    return RebalanceReportResponse(profile_id=profile_id, result=result)


@router.post("/{profile_id}/annual-review", response_model=AnnualReviewResponse)
def annual_review_profile(
    profile_id: int,
    body: AnnualReviewRequest | None = None,
    db: Session = Depends(get_db),
) -> AnnualReviewResponse:
    record = db.get(ProfileRecord, profile_id)
    if not record:
        raise HTTPException(404, "Profile not found")
    profile = Profile.model_validate_json(record.data_json)
    body = body or AnnualReviewRequest()
    result = compute_annual_review(profile, prior_year_return=body.prior_year_return)
    return AnnualReviewResponse(profile_id=profile_id, result=result)


@router.post("/{profile_id}/strategy-compare", response_model=StrategyComparisonResponse)
def strategy_compare_profile(
    profile_id: int,
    body: MonteCarloRequest | None = None,
    db: Session = Depends(get_db),
) -> StrategyComparisonResponse:
    record = db.get(ProfileRecord, profile_id)
    if not record:
        raise HTTPException(404, "Profile not found")
    profile = Profile.model_validate_json(record.data_json)
    body = body or MonteCarloRequest()
    scenario = body.scenario if body.scenario else ScenarioOverrides()
    config = MonteCarloConfig(num_paths=body.num_paths, seed=body.seed)
    result = run_strategy_comparison(profile, scenario, config)
    return StrategyComparisonResponse(profile_id=profile_id, result=result)


@router.post("/scenarios/{scenario_id}/simulate", response_model=SimulateResponse)
def simulate_scenario(scenario_id: int, db: Session = Depends(get_db)) -> SimulateResponse:
    scenario_record = db.get(ScenarioRecord, scenario_id)
    if not scenario_record:
        raise HTTPException(404, "Scenario not found")
    profile_record = db.get(ProfileRecord, scenario_record.profile_id)
    if not profile_record:
        raise HTTPException(404, "Profile not found")
    profile = Profile.model_validate_json(profile_record.data_json)
    scenario = ScenarioOverrides.model_validate_json(scenario_record.data_json)
    result = simulate(profile, scenario)
    return SimulateResponse(profile_id=profile_record.id, result=result)
