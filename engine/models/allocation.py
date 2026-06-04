"""Portfolio allocation targets (Phase 3b)."""

from pydantic import BaseModel, Field, model_validator


class AssetAllocation(BaseModel):
    """Stocks / bonds / cash mix — must sum to 100%."""

    stocks: float = Field(0.55, ge=0, le=1)
    bonds: float = Field(0.40, ge=0, le=1)
    cash: float = Field(0.05, ge=0, le=1)

    @model_validator(mode="after")
    def validate_sum(self) -> AssetAllocation:
        total = self.stocks + self.bonds + self.cash
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Allocation must sum to 100%; got {total * 100:.1f}%")
        return self


DEFAULT_TARGET_ALLOCATION = AssetAllocation()
