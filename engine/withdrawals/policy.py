"""Withdrawal sequencing policies for spending (Phase 2c)."""

from __future__ import annotations

from enum import Enum

from engine.phases.detect import RetirementPhase


class WithdrawalPolicy(str, Enum):
    """How supplemental spending is funded after RMD."""

    PHASE_DEFAULT = "phase_default"
    TAXABLE_FIRST = "taxable_first"
    CASH_FIRST = "cash_first"
    IRA_FIRST = "ira_first"


POLICY_LABELS: dict[WithdrawalPolicy, str] = {
    WithdrawalPolicy.PHASE_DEFAULT: "Phase default (Richer Retirement)",
    WithdrawalPolicy.TAXABLE_FIRST: "Taxable first (all phases)",
    WithdrawalPolicy.CASH_FIRST: "Cash → taxable → IRA → Roth",
    WithdrawalPolicy.IRA_FIRST: "IRA first (all phases)",
}


def fund_spending(
    phase: str,
    remaining_need: float,
    trad: float,
    taxable: float,
    roth: float,
    cash: float,
    *,
    policy: WithdrawalPolicy = WithdrawalPolicy.PHASE_DEFAULT,
) -> tuple[float, float, float, float, float, float, float, float]:
    """
    Phase-aware or fixed-policy withdrawal sequence.
    Returns updated balances, withdrawal amounts, and remaining unfunded need.
    """
    withdrawal_ira = 0.0
    withdrawal_taxable = 0.0
    withdrawal_roth = 0.0

    def take_ira() -> None:
        nonlocal remaining_need, trad, withdrawal_ira
        if remaining_need <= 0 or trad <= 0:
            return
        w = min(trad, remaining_need)
        withdrawal_ira += w
        trad -= w
        remaining_need -= w

    def take_taxable() -> None:
        nonlocal remaining_need, taxable, withdrawal_taxable
        if remaining_need <= 0 or taxable <= 0:
            return
        w = min(taxable, remaining_need)
        withdrawal_taxable += w
        taxable -= w
        remaining_need -= w

    def take_roth() -> None:
        nonlocal remaining_need, roth, withdrawal_roth
        if remaining_need <= 0 or roth <= 0:
            return
        w = min(roth, remaining_need)
        withdrawal_roth += w
        roth -= w
        remaining_need -= w

    def take_cash() -> None:
        nonlocal remaining_need, cash
        if remaining_need <= 0 or cash <= 0:
            return
        w = min(cash, remaining_need)
        cash -= w
        remaining_need -= w

    if policy == WithdrawalPolicy.CASH_FIRST:
        take_cash()
        take_taxable()
        take_ira()
        take_roth()
    elif policy == WithdrawalPolicy.TAXABLE_FIRST:
        take_taxable()
        take_ira()
        take_roth()
        take_cash()
    elif policy == WithdrawalPolicy.IRA_FIRST:
        take_ira()
        take_taxable()
        take_roth()
        take_cash()
    elif phase == RetirementPhase.EARLY_RETIREMENT.value:
        take_taxable()
        take_ira()
        take_roth()
        take_cash()
    elif phase in (RetirementPhase.GOLDEN_YEARS.value, RetirementPhase.PRE_RMD.value):
        take_ira()
        take_taxable()
        take_roth()
        take_cash()
    else:
        take_ira()
        take_roth()
        take_taxable()
        take_cash()

    return (
        trad,
        taxable,
        roth,
        cash,
        withdrawal_ira,
        withdrawal_taxable,
        withdrawal_roth,
        remaining_need,
    )
