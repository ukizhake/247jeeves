from pydantic import BaseModel, Field

from engine.import_.fidelity import FidelityImportResult
from engine.models.profile import Profile, ScenarioOverrides
from engine.models.simulation import MonteCarloResult, SimulationResult


class MonteCarloRequest(BaseModel):
    scenario: ScenarioOverrides | None = None
    num_paths: int = Field(500, ge=50, le=5000)
    seed: int | None = None


class ProfileCreate(Profile):
    pass


class ProfileResponse(BaseModel):
    id: int
    profile: Profile


class ScenarioCreate(BaseModel):
    name: str = "Base case"
    overrides: ScenarioOverrides = ScenarioOverrides()


class ScenarioResponse(BaseModel):
    id: int
    profile_id: int
    name: str
    overrides: ScenarioOverrides


class SimulateRequest(BaseModel):
    scenario: ScenarioOverrides | None = None


class SimulateResponse(BaseModel):
    profile_id: int
    result: SimulationResult


class MonteCarloResponse(BaseModel):
    profile_id: int
    result: MonteCarloResult


class FidelityImportResponse(BaseModel):
    result: FidelityImportResult
