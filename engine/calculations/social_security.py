"""Taxable Social Security — 0% / 50% / 85% tiers (IRS Publication 915 simplified)."""

from engine.facts.loader import load_tax_config
from engine.models.profile import FilingStatus


def _ss_thresholds(filing_status: FilingStatus) -> tuple[float, float]:
    config = load_tax_config()
    key = "mfj" if filing_status == FilingStatus.MFJ else "single"
    row = config["social_security_taxation"][key]
    return float(row["tier1_up_to"]), float(row["tier2_up_to"])


def taxable_social_security(
    social_security_benefits: float,
    other_income: float,
    filing_status: FilingStatus,
) -> float:
    """
    other_income: AGI components excluding Social Security (includes LTCG for provisional income).
    combined_income = other_income + 50% of SS benefits.
    """
    if social_security_benefits <= 0:
        return 0.0

    combined = other_income + 0.5 * social_security_benefits
    tier1, tier2 = _ss_thresholds(filing_status)
    ss = social_security_benefits

    if combined <= tier1:
        return 0.0
    if combined <= tier2:
        return min(0.5 * ss, 0.5 * (combined - tier1))
    return min(0.85 * ss, 0.85 * (combined - tier2) + 0.5 * (tier2 - tier1))
