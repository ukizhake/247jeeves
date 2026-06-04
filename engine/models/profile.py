from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic import ValidationInfo

from engine.models.allocation import AssetAllocation, DEFAULT_TARGET_ALLOCATION

# Generous cap — ~$6,667/mo at age 70 for high earners who delay to 70.
MAX_SS_ANNUAL_PER_PERSON = 80_000
MAX_SS_MONTHLY = 6_500


def validate_social_security_annual(value: float, *, label: str = "Social Security") -> float:
    """Reject implausible Social Security amounts — no silent auto-correction."""
    if value <= 0:
        return 0.0
    v = float(value)
    monthly = v / 12

    if monthly > MAX_SS_MONTHLY:
        raise ValueError(
            f"{label}: ${monthly:,.0f}/mo looks too high (you entered ${v:,.0f}/yr). "
            "Use the monthly amount from ssa.gov (typically $1,500–$5,500/mo) and re-enter."
        )

    if v > MAX_SS_ANNUAL_PER_PERSON:
        raise ValueError(
            f"{label}: ${v:,.0f}/yr looks too high. "
            "Enter the monthly ssa.gov benefit, not the annual amount, and re-enter."
        )

    return v


class FilingStatus(str, Enum):
    SINGLE = "single"
    MFJ = "mfj"


class Accounts(BaseModel):
    traditional_ira: float = Field(0, ge=0)
    roth_ira: float = Field(0, ge=0)
    taxable: float = Field(0, ge=0)
    cash: float = Field(0, ge=0)


class IncomeSources(BaseModel):
    rental: float = Field(0, ge=0)
    pension: float = Field(0, ge=0)
    dividends: float = Field(0, ge=0)
    qualified_dividend_ratio: float = Field(
        0.9,
        ge=0,
        le=1,
        description="Share of dividends taxed as LTCG / qualified dividends",
    )
    consulting: float = Field(0, ge=0)
    other_ordinary: float = Field(0, ge=0)


class Profile(BaseModel):
    """User retirement profile — manual inputs for Phase 1."""

    name: str = "My Plan"
    age: int = Field(..., ge=18, le=100)
    plan_to_age: int = Field(
        95,
        ge=62,
        le=105,
        description="Last age to include in the projection (inclusive)",
    )
    spouse_age: Optional[int] = Field(None, ge=18, le=100)
    filing_status: FilingStatus = FilingStatus.MFJ
    state: Optional[str] = None

    accounts: Accounts = Field(default_factory=Accounts)
    income: IncomeSources = Field(default_factory=IncomeSources)

    annual_spending: float = Field(..., gt=0)
    consulting_stop_age: int = Field(
        70,
        ge=50,
        le=80,
        description="Stop consulting/earned income at this age (exclusive)",
    )
    social_security_claim_age: int = Field(70, ge=62, le=70)
    social_security_annual_at_claim: float = Field(
        0,
        ge=0,
        description="Your annual benefit at claim age (ssa.gov monthly × 12)",
    )
    spouse_social_security_annual_at_claim: float = Field(
        0,
        ge=0,
        description="Spouse annual benefit at claim (MFJ); added to household SS",
    )
    spouse_social_security_claim_age: Optional[int] = Field(
        None,
        ge=62,
        le=70,
        description="Spouse claim age; each person's SS starts when they reach this age",
    )
    social_security_cola_rate: Optional[float] = Field(
        None,
        ge=0,
        le=0.1,
        description="Annual COLA on benefits after claiming; defaults to inflation_rate",
    )

    projection_start_year: int = Field(
        2026,
        ge=2020,
        le=2100,
        description="Calendar year when profile ages apply (year 1 of the projection)",
    )

    return_rate: float = Field(0.06, ge=0, le=0.2)
    return_volatility: float = Field(
        0.15,
        ge=0,
        le=0.5,
        description="Annual return std dev for Monte Carlo (e.g. 0.15 = 15%)",
    )
    inflation_rate: float = Field(0.03, ge=0, le=0.1)
    withdrawal_scheme: Literal[
        "cola",
        "fixed_annuity",
        "performance_cola",
        "fixed_percentage",
        "floor_ceiling",
    ] = Field(
        "performance_cola",
        description="COLA, book FA, performance COLA, FP, or floor & ceiling (F&C)",
    )
    initial_withdrawal_rate: float = Field(
        0.047,
        ge=0.02,
        le=0.2,
        description="FP scheme: annual spending as fraction of start-of-year wealth (e.g. 0.047 = 4.7%)",
    )
    spending_cola_rate: Optional[float] = Field(
        None,
        ge=0,
        le=0.1,
        description="Annual spending COLA; defaults to inflation_rate",
    )
    annuity_product_type: Literal["none", "pension", "spira", "mixed"] = Field(
        "none",
        description="Insurance SPIA vs pension floor — educational label (Phase 3d)",
    )
    spira_premium_paid: float = Field(
        0,
        ge=0,
        description="Hypothetical lump sum moved to SPIA (reduces investable accounts in comparisons)",
    )
    spira_payout_rate: float = Field(
        0.06,
        ge=0.02,
        le=0.15,
        description="Estimated annual SPIA payout ÷ premium (quote from insurer; default 6%)",
    )
    annuity_income_annual: float = Field(
        0,
        ge=0,
        description="Guaranteed annual income (SPIA, pension floor, etc.) offsetting portfolio withdrawals",
    )
    annuity_cola_rate: Optional[float] = Field(
        None,
        ge=0,
        le=0.1,
        description="Annual increase on annuity income; None = fixed nominal",
    )
    annual_review_month: int = Field(
        10,
        ge=1,
        le=12,
        description="Month for annual spending review (10 = October)",
    )
    performance_skip_cola_after_down_year: bool = Field(
        True,
        description="Hold spending flat after a down portfolio year (performance COLA)",
    )
    performance_max_raise_pct: Optional[float] = Field(
        None,
        ge=0,
        le=0.5,
        description="Optional cap on year-over-year spending increase (e.g. 0.10 = 10%)",
    )
    performance_max_cut_pct: Optional[float] = Field(
        None,
        ge=0,
        le=0.5,
        description="Optional cap on year-over-year spending cut",
    )
    floor_ceiling_raise_pct: float = Field(
        0.10,
        ge=0,
        le=0.5,
        description="F&C scheme: max year-over-year spending increase vs prior year",
    )
    floor_ceiling_cut_pct: float = Field(
        0.10,
        ge=0,
        le=0.5,
        description="F&C scheme: max year-over-year spending decrease vs prior year",
    )
    taxable_cost_basis_ratio: float = Field(
        0.8,
        ge=0,
        le=1,
        description="Fraction of taxable withdrawal treated as basis (not gain)",
    )
    target_allocation: AssetAllocation = Field(
        default_factory=lambda: DEFAULT_TARGET_ALLOCATION.model_copy(),
        description="Target portfolio mix (deck default 55/40/5 stocks/bonds/cash)",
    )
    current_allocation: Optional[AssetAllocation] = Field(
        None,
        description="Actual mix today; if omitted, inferred from cash balance vs target",
    )
    rebalance_band_pct: float = Field(
        0.02,
        ge=0,
        le=0.1,
        description="Skip rebalance trades when every sleeve is within this drift (e.g. 0.02 = 2%)",
    )
    shiller_cape: Optional[float] = Field(
        None,
        ge=5,
        le=60,
        description="Current Shiller CAPE for SAFEMAX education (multpl.com/shiller-pe); omit for default",
    )
    inflation_regime: Literal["normal", "high"] = Field(
        "normal",
        description="Deck inflation regime for CAPE→SAFEMAX estimate (high subtracts ~1%)",
    )

    @field_validator("social_security_annual_at_claim", "spouse_social_security_annual_at_claim")
    @classmethod
    def validate_ss_annual(cls, v: float, info: ValidationInfo) -> float:
        label = (
            "Your Social Security"
            if info.field_name == "social_security_annual_at_claim"
            else "Spouse Social Security"
        )
        return validate_social_security_annual(v, label=label)


class ScenarioOverrides(BaseModel):
    """What-if knobs for a scenario run."""

    name: str = "Base case"
    return_scenario: Literal["base", "bad_early", "flat_low"] = Field(
        "base",
        description="Deterministic return path: base | bad_early | flat_low",
    )
    net_portfolio_income: bool = Field(
        True,
        description="Reduce spending withdrawals by portfolio income (dividends, rental, SS, etc.)",
    )
    horizon_years: Optional[int] = Field(
        None,
        ge=1,
        le=60,
        description="Explicit year count; if omitted, uses plan_to_age from profile/scenario",
    )
    plan_to_age: Optional[int] = Field(None, ge=62, le=105)
    roth_conversion_annual: Optional[float] = Field(
        None,
        ge=0,
        description="Fixed annual conversion; None = engine suggests via rules",
    )
    spending_override: Optional[float] = Field(None, gt=0)
    social_security_claim_age_override: Optional[int] = Field(None, ge=62, le=70)
    target_bracket_rate: float = Field(
        0.22,
        description="Target marginal bracket ceiling for Roth conversions",
    )
    withdrawal_policy: Literal[
        "phase_default",
        "taxable_first",
        "cash_first",
        "ira_first",
    ] = Field(
        "phase_default",
        description="Withdrawal order for supplemental spending (Phase 2c)",
    )
    spending_scheme_override: Optional[
        Literal[
            "cola",
            "fixed_annuity",
            "performance_cola",
            "fixed_percentage",
            "floor_ceiling",
        ]
    ] = Field(
        None,
        description="Override profile withdrawal_scheme for this scenario run (Phase 3c)",
    )
