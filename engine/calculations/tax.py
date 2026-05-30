"""Federal income tax with ordinary/LTCG stacking and senior deductions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.calculations.niit import compute_niit
from engine.calculations.social_security import taxable_social_security
from engine.facts.loader import load_tax_config
from engine.models.profile import FilingStatus, Profile


def _status_key(filing_status: FilingStatus) -> str:
    return "mfj" if filing_status == FilingStatus.MFJ else "single"


def _brackets(filing_status: FilingStatus) -> list[dict[str, Any]]:
    config = load_tax_config()
    return config["brackets"][_status_key(filing_status)]


def _ltcg_limits(filing_status: FilingStatus) -> tuple[float, float]:
    config = load_tax_config()
    row = config["ltcg_brackets"][_status_key(filing_status)]
    return float(row["zero_pct_up_to"]), float(row["fifteen_pct_up_to"])


def standard_deduction(filing_status: FilingStatus) -> float:
    config = load_tax_config()
    return float(config["standard_deduction"][_status_key(filing_status)])


def spouse_age_at(profile: Profile, primary_age: int) -> int | None:
    """Spouse age in the same projection year as primary_age."""
    if profile.spouse_age is None:
        return None
    return profile.spouse_age + (primary_age - profile.age)


def count_seniors(profile: Profile, age: int) -> int:
    """Taxpayers age 65+ eligible for additional + senior deductions."""
    n = 1 if age >= 65 else 0
    if profile.filing_status == FilingStatus.MFJ:
        s_age = spouse_age_at(profile, age)
        if s_age is not None:
            if s_age >= 65:
                n += 1
        elif age >= 65:
            # MFJ without spouse age — assume spouse similar if primary is 65+
            n = 2
    return n


def total_deductions(profile: Profile, age: int) -> float:
    """Standard + additional (65+) + senior deduction (Richer Retirement Ch. 8–12)."""
    config = load_tax_config()
    base = standard_deduction(profile.filing_status)
    seniors = count_seniors(profile, age)
    additional = float(config.get("additional_standard_deduction_65", 1600)) * seniors
    senior = float(config.get("senior_deduction_per_person", 6000)) * seniors
    return base + additional + senior


def compute_ordinary_tax(ordinary_taxable: float, filing_status: FilingStatus) -> float:
    if ordinary_taxable <= 0:
        return 0.0
    brackets = _brackets(filing_status)
    tax = 0.0
    lower = 0.0
    for bracket in brackets:
        upper = bracket["up_to"]
        rate = bracket["rate"]
        if upper is None:
            tax += (ordinary_taxable - lower) * rate
            break
        cap = min(ordinary_taxable, float(upper))
        if cap > lower:
            tax += (cap - lower) * rate
        if ordinary_taxable <= float(upper):
            break
        lower = float(upper)
    return max(0.0, tax)


def compute_ltcg_tax(
    ordinary_taxable: float,
    ltcg: float,
    filing_status: FilingStatus,
) -> float:
    """LTCG stacked on top of ordinary taxable income (Richer Retirement Ch. 7)."""
    if ltcg <= 0:
        return 0.0
    zero_end, fifteen_end = _ltcg_limits(filing_status)
    in_zero = max(0.0, min(ltcg, zero_end - ordinary_taxable))
    remaining = ltcg - in_zero
    in_fifteen = max(0.0, min(remaining, fifteen_end - max(ordinary_taxable, zero_end)))
    remaining -= in_fifteen
    return in_zero * 0.0 + in_fifteen * 0.15 + remaining * 0.20


@dataclass
class FederalTaxResult:
    agi: float
    ordinary_income: float
    long_term_capital_gains: float
    social_security_gross: float
    social_security_taxable: float
    net_investment_income: float
    total_deductions: float
    ordinary_taxable: float
    total_taxable_income: float
    ordinary_tax: float
    ltcg_tax: float
    niit_tax: float
    income_tax: float
    federal_tax: float
    marginal_ordinary_rate: float
    bracket_room_12: float
    bracket_room_22: float
    bracket_room_24: float
    niit_warning: bool


def compute_federal_tax_stacked(
    ordinary_income: float,
    long_term_capital_gains: float,
    profile: Profile,
    age: int,
    *,
    social_security_gross: float = 0.0,
    net_investment_income: float | None = None,
) -> FederalTaxResult:
    """
    ordinary_income: income before taxable Social Security is applied.
    long_term_capital_gains: net LTCG + qualified dividends.
    """
    other_for_ss = ordinary_income + long_term_capital_gains
    ss_taxable = taxable_social_security(
        social_security_gross, other_for_ss, profile.filing_status
    )
    ordinary_with_ss = ordinary_income + ss_taxable

    deductions = total_deductions(profile, age)
    ltcg = long_term_capital_gains
    ordinary_taxable = max(0.0, ordinary_with_ss - deductions)
    if ordinary_taxable < 0:
        ltcg = max(0.0, ltcg + ordinary_taxable)
        ordinary_taxable = 0.0

    ordinary_tax = compute_ordinary_tax(ordinary_taxable, profile.filing_status)
    ltcg_tax = compute_ltcg_tax(ordinary_taxable, ltcg, profile.filing_status)
    total_taxable = ordinary_taxable + ltcg
    agi = ordinary_with_ss + ltcg

    nii = net_investment_income if net_investment_income is not None else ltcg
    niit = compute_niit(agi, nii, profile.filing_status)
    income_tax = ordinary_tax + ltcg_tax
    federal = income_tax + niit

    return FederalTaxResult(
        agi=agi,
        ordinary_income=ordinary_with_ss,
        long_term_capital_gains=ltcg,
        social_security_gross=social_security_gross,
        social_security_taxable=ss_taxable,
        net_investment_income=nii,
        total_deductions=deductions,
        ordinary_taxable=ordinary_taxable,
        total_taxable_income=total_taxable,
        ordinary_tax=ordinary_tax,
        ltcg_tax=ltcg_tax,
        niit_tax=niit,
        income_tax=income_tax,
        federal_tax=federal,
        marginal_ordinary_rate=marginal_rate(ordinary_taxable, profile.filing_status),
        bracket_room_12=bracket_room(ordinary_taxable, profile.filing_status, 0.12),
        bracket_room_22=bracket_room(ordinary_taxable, profile.filing_status, 0.22),
        bracket_room_24=bracket_room(ordinary_taxable, profile.filing_status, 0.24),
        niit_warning=niit > 0,
    )


# --- Legacy helpers (used by rules / simple paths) ---


def compute_federal_tax(taxable_income: float, filing_status: FilingStatus) -> float:
    return compute_ordinary_tax(taxable_income, filing_status)


def marginal_rate(taxable_income: float, filing_status: FilingStatus) -> float:
    if taxable_income <= 0:
        return 0.10
    brackets = _brackets(filing_status)
    for bracket in brackets:
        upper = bracket["up_to"]
        if upper is None or taxable_income <= float(upper):
            return float(bracket["rate"])
    return 0.37


def bracket_top_for_rate(target_rate: float, filing_status: FilingStatus) -> float:
    brackets = _brackets(filing_status)
    for bracket in brackets:
        if float(bracket["rate"]) == target_rate:
            up = bracket["up_to"]
            return float(up) if up is not None else 1_000_000_000.0
    prev_top = 0.0
    for bracket in brackets:
        if float(bracket["rate"]) <= target_rate and bracket["up_to"] is not None:
            prev_top = float(bracket["up_to"])
    return prev_top


def bracket_room(
    ordinary_taxable: float,
    filing_status: FilingStatus,
    target_rate: float,
) -> float:
    top = bracket_top_for_rate(target_rate, filing_status)
    return max(0.0, top - ordinary_taxable)


def taxable_income_from_agi(agi: float, filing_status: FilingStatus) -> float:
    return max(0.0, agi - standard_deduction(filing_status))
