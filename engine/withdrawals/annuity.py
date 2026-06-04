"""Insurance annuity (SPIA) vs book FA spending — Phase 3d."""

from __future__ import annotations

from pydantic import BaseModel, Field

from engine.models.profile import Accounts, Profile


class AnnuityYearOneSnapshot(BaseModel):
    variant: str
    label: str
    total_wealth: float
    annual_spending_target: float
    annuity_income: float
    portfolio_withdrawal_estimate: float
    income_coverage_pct: float
    withdrawal_scheme: str
    notes: str = ""


class AnnuityEducationResult(BaseModel):
    book_fa_explanation: str
    spira_explanation: str
    year_one_snapshots: list[AnnuityYearOneSnapshot]
    suggestions: list[str] = Field(default_factory=list)


def total_wealth(accounts: Accounts) -> float:
    return (
        accounts.traditional_ira
        + accounts.roth_ira
        + accounts.taxable
        + accounts.cash
    )


def apply_spira_premium(profile: Profile) -> Profile:
    """
    Model a one-time SPIA purchase: reduce investable balances, add guaranteed payout.
    Premium is taken proportionally from trad / roth / taxable / cash.
    """
    premium = profile.spira_premium_paid
    if premium <= 0:
        return profile

    a = profile.accounts
    total = total_wealth(a)
    if total <= 0:
        return profile
    if premium >= total:
        premium = total * 0.95

    scale = (total - premium) / total
    payout = profile.annuity_income_annual
    if payout <= 0 and profile.spira_payout_rate > 0:
        payout = premium * profile.spira_payout_rate

    new_accounts = Accounts(
        traditional_ira=round(a.traditional_ira * scale, 2),
        roth_ira=round(a.roth_ira * scale, 2),
        taxable=round(a.taxable * scale, 2),
        cash=round(a.cash * scale, 2),
    )
    return profile.model_copy(
        update={
            "accounts": new_accounts,
            "annuity_income_annual": round(payout, 2),
            "annuity_product_type": "spira",
        }
    )


def estimate_year_one_snapshot(
    profile: Profile,
    *,
    variant: str,
    label: str,
    scheme: str,
    notes: str = "",
) -> AnnuityYearOneSnapshot:
    from engine.withdrawals.spending import spending_for_year

    wealth = total_wealth(profile.accounts)
    spend, _ = spending_for_year(
        profile,
        0,
        base_annual=profile.annual_spending,
        prior_spending=profile.annual_spending,
        prior_year_return=None,
        wealth_start=wealth,
    )
    annuity = profile.annuity_income_annual
    port_inc = (
        profile.income.rental
        + profile.income.dividends
        + profile.income.pension
        + profile.income.consulting
        + profile.income.other_ordinary
    )
    port_wd = max(0.0, spend - port_inc - annuity)
    coverage = (annuity / spend * 100) if spend > 0 else 0.0

    return AnnuityYearOneSnapshot(
        variant=variant,
        label=label,
        total_wealth=round(wealth, 2),
        annual_spending_target=round(spend, 2),
        annuity_income=round(annuity, 2),
        portfolio_withdrawal_estimate=round(port_wd, 2),
        income_coverage_pct=round(coverage, 1),
        withdrawal_scheme=scheme,
        notes=notes,
    )


def compute_annuity_education(profile: Profile) -> AnnuityEducationResult:
    """Explain book FA vs SPIA and show year-one funding snapshots."""
    base = profile
    book_fa = base.model_copy(
        update={
            "withdrawal_scheme": "fixed_annuity",
            "annuity_income_annual": 0,
            "annuity_product_type": "none",
        }
    )
    spira = apply_spira_premium(base) if base.spira_premium_paid > 0 else None

    snapshots = [
        estimate_year_one_snapshot(
            base,
            variant="current",
            label="Your plan (current scheme)",
            scheme=base.withdrawal_scheme,
            notes="Portfolio spending path + any annuity floor already entered.",
        ),
        estimate_year_one_snapshot(
            book_fa,
            variant="book_fa",
            label="Book FA only (nominal lifestyle)",
            scheme="fixed_annuity",
            notes="Deck FA scheme: same dollar spending every year from the portfolio — not an insurance product.",
        ),
    ]
    if spira is not None:
        snapshots.append(
            estimate_year_one_snapshot(
                spira,
                variant="spira",
                label="With modeled SPIA purchase",
                scheme=spira.withdrawal_scheme,
                notes=(
                    f"Premium ${base.spira_premium_paid:,.0f} removed from investable accounts; "
                    f"payout ${spira.annuity_income_annual:,.0f}/yr offsets withdrawals."
                ),
            )
        )

    suggestions = [
        "Book FA (fixed_annuity scheme) controls how fast lifestyle spending rises from the portfolio.",
        "Insurance SPIA / pension is guaranteed income that reduces how much you pull from accounts.",
        "You can combine them: e.g. performance COLA spending plus an annuity floor.",
    ]
    if base.spira_premium_paid <= 0:
        suggestions.append(
            "Enter a hypothetical SPIA premium to see investable wealth after annuitization."
        )
    if base.annuity_income_annual > 0 and base.withdrawal_scheme == "fixed_annuity":
        suggestions.append(
            "You have both book FA scheme and annuity income — confirm that matches your intent."
        )

    return AnnuityEducationResult(
        book_fa_explanation=(
            "Fixed annuity (FA) withdrawal scheme: keep the same nominal annual spending from "
            "your portfolio each year (no inflation bump). This is a spreadsheet rule from "
            "A Richer Retirement — not buying an insurance annuity."
        ),
        spira_explanation=(
            "Insurance SPIA: exchange a lump sum for guaranteed lifetime income. In the model, "
            "premium reduces IRA/brokerage balances and annuity_income_annual offsets portfolio withdrawals."
        ),
        year_one_snapshots=snapshots,
        suggestions=suggestions,
    )
