"""Parse Fidelity Portfolio Positions CSV exports."""

from __future__ import annotations

import csv
import io
import re
from enum import Enum

from pydantic import BaseModel, Field


class AccountBucket(str, Enum):
    TAXABLE = "taxable"
    TRADITIONAL_IRA = "traditional_ira"
    ROTH_IRA = "roth_ira"
    CASH = "cash"
    UNKNOWN = "unknown"


MONEY_MARKET_SYMBOLS = ("FDRXX", "FCASH", "SPAXX", "FZFXX", "SPRXX")


class FidelityHolding(BaseModel):
    account_number: str
    account_name: str
    symbol: str
    description: str
    quantity: float = 0
    current_value: float = 0
    cost_basis: float = 0
    bucket: AccountBucket


class FidelityAccountSummary(BaseModel):
    account_number: str
    account_name: str
    bucket: AccountBucket
    total_value: float
    cost_basis: float = 0


class FidelityImportResult(BaseModel):
    as_of: str | None = None
    accounts: list[FidelityAccountSummary]
    holdings: list[FidelityHolding]
    traditional_ira: float = 0
    roth_ira: float = 0
    taxable: float = 0
    cash: float = 0
    taxable_cost_basis_ratio: float = Field(
        0.8,
        description="Cost basis / market value on taxable accounts only",
    )
    total_value: float = 0
    position_count: int = 0


def _parse_money(raw: str | None) -> float:
    if not raw or raw.strip() in ("", "--", "N/A"):
        return 0.0
    cleaned = raw.strip().replace("$", "").replace(",", "").replace("+", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_quantity(raw: str | None) -> float:
    if not raw or raw.strip() in ("", "--"):
        return 0.0
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return 0.0


def _is_money_market(symbol: str) -> bool:
    sym = symbol.upper().replace("*", "")
    return any(sym.startswith(prefix) for prefix in MONEY_MARKET_SYMBOLS)


def _classify_account(account_name: str) -> AccountBucket:
    name = account_name.upper()
    if "ROTH" in name and "IRA" in name:
        return AccountBucket.ROTH_IRA
    if "401" in name or "ROLLOVER IRA" in name or "TRADITIONAL IRA" in name:
        return AccountBucket.TRADITIONAL_IRA
    if "INDIVIDUAL" in name or "JOINT" in name or "BROKERAGE" in name:
        return AccountBucket.TAXABLE
    return AccountBucket.UNKNOWN


def _extract_as_of(text: str) -> str | None:
    match = re.search(r"Date downloaded\s+(.+?)(?:\n|$)", text, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip().strip('"')


def _row_value(row: dict[str, str | None], *keys: str) -> str:
    for key in keys:
        if key in row and row[key]:
            return row[key].strip()
    return ""


def parse_fidelity_csv(text: str) -> FidelityImportResult:
    """Parse Fidelity 'Portfolio_Positions' CSV export."""
    text = text.lstrip("\ufeff")
    lines: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith('"') and not line.startswith('"Account'):
            continue
        lines.append(line)

    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    if reader.fieldnames:
        reader.fieldnames = [name.lstrip("\ufeff") for name in reader.fieldnames]

    holdings: list[FidelityHolding] = []
    account_totals: dict[tuple[str, str], dict[str, float]] = {}

    for row in reader:
        account_number = _row_value(row, "Account Number")
        account_name = _row_value(row, "Account Name")
        symbol = _row_value(row, "Symbol")
        if not account_number or not symbol:
            continue

        value = _parse_money(_row_value(row, "Current Value"))
        basis = _parse_money(_row_value(row, "Cost Basis Total"))
        acct_bucket = _classify_account(account_name)
        bucket = AccountBucket.CASH if _is_money_market(symbol) else acct_bucket

        holdings.append(
            FidelityHolding(
                account_number=account_number,
                account_name=account_name,
                symbol=symbol,
                description=_row_value(row, "Description"),
                quantity=_parse_quantity(_row_value(row, "Quantity")),
                current_value=value,
                cost_basis=basis,
                bucket=bucket,
            )
        )

        key = (account_number, account_name)
        if key not in account_totals:
            account_totals[key] = {
                "value": 0.0,
                "basis": 0.0,
                "cash_sweep": 0.0,
                "taxable_basis": 0.0,
                "taxable_value": 0.0,
            }
        account_totals[key]["value"] += value
        account_totals[key]["basis"] += basis
        if _is_money_market(symbol):
            account_totals[key]["cash_sweep"] += value
        elif acct_bucket == AccountBucket.TAXABLE:
            account_totals[key]["taxable_basis"] += basis
            account_totals[key]["taxable_value"] += value

    accounts: list[FidelityAccountSummary] = []
    trad = roth = taxable = cash = 0.0
    taxable_basis = taxable_value = 0.0

    for (acct_num, acct_name), totals in account_totals.items():
        bucket = _classify_account(acct_name)
        accounts.append(
            FidelityAccountSummary(
                account_number=acct_num,
                account_name=acct_name,
                bucket=bucket,
                total_value=round(totals["value"], 2),
                cost_basis=round(totals["basis"], 2),
            )
        )
        sweep = totals["cash_sweep"]
        investable = totals["value"] - sweep
        cash += sweep
        if bucket == AccountBucket.TRADITIONAL_IRA:
            trad += investable
        elif bucket == AccountBucket.ROTH_IRA:
            roth += investable
        elif bucket == AccountBucket.TAXABLE:
            taxable += investable
            taxable_basis += totals["taxable_basis"]
            taxable_value += totals["taxable_value"]

    basis_ratio = 0.8
    if taxable_value > 0 and taxable_basis > 0:
        basis_ratio = min(1.0, max(0.0, taxable_basis / taxable_value))

    total = trad + roth + taxable + cash
    return FidelityImportResult(
        as_of=_extract_as_of(text),
        accounts=sorted(accounts, key=lambda a: -a.total_value),
        holdings=holdings,
        traditional_ira=round(trad, 2),
        roth_ira=round(roth, 2),
        taxable=round(taxable, 2),
        cash=round(cash, 2),
        taxable_cost_basis_ratio=round(basis_ratio, 4),
        total_value=round(total, 2),
        position_count=len(holdings),
    )
