from engine.calculations.niit import compute_niit
from engine.calculations.rmd import compute_rmd
from engine.calculations.social_security import taxable_social_security
from engine.calculations.tax import (
    FederalTaxResult,
    bracket_room,
    compute_federal_tax,
    compute_federal_tax_stacked,
    marginal_rate,
    total_deductions,
)

__all__ = [
    "FederalTaxResult",
    "bracket_room",
    "compute_federal_tax",
    "compute_federal_tax_stacked",
    "compute_niit",
    "compute_rmd",
    "marginal_rate",
    "taxable_social_security",
    "total_deductions",
]
