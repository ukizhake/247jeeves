"""Target allocation drift and annual rebalance report (Phase 3b)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from engine.models.allocation import DEFAULT_TARGET_ALLOCATION, AssetAllocation
from engine.models.profile import Profile


class AllocationSlice(BaseModel):
    asset: str
    target_pct: float
    current_pct: float
    target_dollars: float
    current_dollars: float
    drift_dollars: float
    drift_pct: float


class RebalanceTrade(BaseModel):
    asset: str
    action: str  # buy | sell
    amount: float
    preferred_location: str  # tax_advantaged | taxable | cash


class RebalanceReport(BaseModel):
    total_wealth: float
    tax_advantaged_balance: float
    taxable_balance: float
    cash_balance: float
    target: AssetAllocation
    current: AssetAllocation
    slices: list[AllocationSlice]
    trades: list[RebalanceTrade]
    max_drift_pct: float
    needs_rebalance: bool
    rebalance_in_tax_advantaged: float
    rebalance_notes: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


def total_wealth(profile: Profile) -> float:
    a = profile.accounts
    return a.traditional_ira + a.roth_ira + a.taxable + a.cash


def _infer_current_allocation(profile: Profile, wealth: float) -> AssetAllocation:
    """When user has not set current mix, infer cash from account; rest is stocks/bonds split."""
    if profile.current_allocation is not None:
        return profile.current_allocation
    cash_pct = (profile.accounts.cash / wealth) if wealth > 0 else 0.0
    remainder = max(0.0, 1.0 - cash_pct)
    target = profile.target_allocation or DEFAULT_TARGET_ALLOCATION
    stock_share = target.stocks / max(target.stocks + target.bonds, 1e-9)
    return AssetAllocation(
        stocks=remainder * stock_share,
        bonds=remainder * (1 - stock_share),
        cash=cash_pct,
    )


def _build_trades(
    slices: list[AllocationSlice],
    *,
    tax_adv: float,
    taxable: float,
) -> tuple[list[RebalanceTrade], float, list[str]]:
    # Positive drift = overweight vs target → sell; negative = underweight → buy.
    sells = [(s.asset, s.drift_dollars) for s in slices if s.drift_dollars > 1]
    buys = [(s.asset, -s.drift_dollars) for s in slices if s.drift_dollars < -1]
    notes: list[str] = []
    trades: list[RebalanceTrade] = []

    for asset, amount in sells:
        loc = "tax_advantaged" if tax_adv >= amount else "taxable"
        if loc == "taxable" and taxable > 0:
            notes.append(f"Sell {asset} inside IRA/Roth when possible — avoids taxable gains.")
        trades.append(
            RebalanceTrade(
                asset=asset,
                action="sell",
                amount=round(amount, 2),
                preferred_location=loc,
            )
        )

    for asset, amount in buys:
        in_ira = min(amount, tax_adv)
        trades.append(
            RebalanceTrade(
                asset=asset,
                action="buy",
                amount=round(amount, 2),
                preferred_location="tax_advantaged" if in_ira >= amount * 0.5 else "taxable",
            )
        )

    rebalance_in_adv = sum(t.amount for t in trades if t.preferred_location == "tax_advantaged")
    return trades, rebalance_in_adv, notes


def compute_rebalance_report(profile: Profile) -> RebalanceReport:
    """
    Compare current vs target allocation and suggest annual rebalance trades.
    Deck default: 55% stocks / 40% bonds / 5% cash (five stock classes @ 11% each).
    """
    wealth = total_wealth(profile)
    target = profile.target_allocation or DEFAULT_TARGET_ALLOCATION
    current = _infer_current_allocation(profile, wealth)

    a = profile.accounts
    tax_adv = a.traditional_ira + a.roth_ira
    taxable = a.taxable
    cash_acct = a.cash

    slices: list[AllocationSlice] = []
    for asset, t_pct, c_pct in (
        ("stocks", target.stocks, current.stocks),
        ("bonds", target.bonds, current.bonds),
        ("cash", target.cash, current.cash),
    ):
        t_d = wealth * t_pct
        c_d = wealth * c_pct
        drift = c_d - t_d
        slices.append(
            AllocationSlice(
                asset=asset,
                target_pct=round(t_pct, 4),
                current_pct=round(c_pct, 4),
                target_dollars=round(t_d, 2),
                current_dollars=round(c_d, 2),
                drift_dollars=round(drift, 2),
                drift_pct=round(c_pct - t_pct, 4),
            )
        )

    max_drift = max(abs(s.drift_pct) for s in slices) if slices else 0.0
    band = profile.rebalance_band_pct
    needs = max_drift > band

    trades, rebalance_in_adv, trade_notes = _build_trades(
        slices, tax_adv=tax_adv, taxable=taxable
    ) if needs and wealth > 0 else ([], 0.0, [])

    suggestions: list[str] = []
    if profile.current_allocation is None:
        suggestions.append(
            "Current allocation was inferred from your cash balance and target stock/bond split — "
            "enter actual stocks/bonds/cash % for a precise rebalance report."
        )
    suggestions.append(
        "Richer Retirement: rebalance inside Traditional IRA and Roth IRA first; "
        "avoid realizing gains in taxable brokerage (Principle 5)."
    )
    if tax_adv <= 0 and needs:
        suggestions.append(
            "No tax-advantaged balance — bond/stock shifts in taxable may trigger capital gains."
        )
    if max_drift <= band:
        suggestions.append(f"Within {band * 100:.0f}% band — no trades required this year.")
    suggestions.append(
        "Deck default: 55% stocks (five stock asset classes equally @ 11% each), "
        "40% intermediate government bonds, 5% Treasury bills / cash."
    )

    notes = trade_notes.copy()
    if needs and profile.annual_review_month == 10:
        notes.append("Pair with October annual spending review (Phase 3a).")

    return RebalanceReport(
        total_wealth=round(wealth, 2),
        tax_advantaged_balance=round(tax_adv, 2),
        taxable_balance=round(taxable, 2),
        cash_balance=round(cash_acct, 2),
        target=target,
        current=current,
        slices=slices,
        trades=trades,
        max_drift_pct=round(max_drift, 4),
        needs_rebalance=needs,
        rebalance_in_tax_advantaged=round(rebalance_in_adv, 2),
        rebalance_notes=notes,
        suggestions=suggestions,
    )
