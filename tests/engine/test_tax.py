from engine.calculations.tax import compute_federal_tax
from engine.models.profile import FilingStatus


def test_zero_taxable_income():
    assert compute_federal_tax(0, FilingStatus.MFJ) == 0


def test_positive_tax_mfj():
    tax = compute_federal_tax(100_000, FilingStatus.MFJ)
    assert tax > 0
