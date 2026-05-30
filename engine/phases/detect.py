from enum import Enum

from engine.calculations.rmd import rmd_start_age


class RetirementPhase(str, Enum):
    """Aligned with Richer Retirement drawdown phases (slides 39–42)."""

    EARLY_RETIREMENT = "early_retirement"  # retirement through age 65
    GOLDEN_YEARS = "golden_years"  # ages 66–69
    PRE_RMD = "pre_rmd"  # age 70 until RMD start (typically 75)
    RMD_YEARS = "rmd_years"
    WIDOW = "widow"


def detect_phase(age: int, social_security_started: bool = False) -> RetirementPhase:
    rmd_age = rmd_start_age()
    if age >= rmd_age:
        return RetirementPhase.RMD_YEARS
    if age >= 70:
        return RetirementPhase.PRE_RMD
    if age >= 66:
        return RetirementPhase.GOLDEN_YEARS
    return RetirementPhase.EARLY_RETIREMENT
