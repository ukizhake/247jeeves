"""Net Investment Income Tax — 3.8% on investment income above MAGI threshold."""

from engine.facts.loader import load_tax_config
from engine.models.profile import FilingStatus


def niit_magi_threshold(filing_status: FilingStatus) -> float:
    config = load_tax_config()
    key = "mfj" if filing_status == FilingStatus.MFJ else "single"
    return float(config["niit"]["magi_threshold"][key])


def niit_rate() -> float:
    return float(load_tax_config()["niit"]["rate"])


def compute_niit(
    magi: float,
    net_investment_income: float,
    filing_status: FilingStatus,
) -> float:
    """
    NIIT = 3.8% × lesser of (net investment income) or (MAGI − threshold).
    MAGI modeled as AGI for Phase 1.
    """
    if net_investment_income <= 0:
        return 0.0
    threshold = niit_magi_threshold(filing_status)
    excess_magi = max(0.0, magi - threshold)
    base = min(net_investment_income, excess_magi)
    return round(base * niit_rate(), 2)
