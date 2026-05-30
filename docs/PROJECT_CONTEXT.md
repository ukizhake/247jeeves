# Project context (sanitized)

Engineering decisions and mental model for outlast.money. **No personal portfolio data** — safe to keep in repo and reference in new Cursor chats.

## What this app is

Local-first retirement tax simulator. Four account buckets only: Traditional IRA, Roth IRA, taxable brokerage, cash. Rules engine recommends tactics from Richer Retirement-style YAML rules. Data stays in local SQLite (`outlast.db`, gitignored).

## Key design decisions

### Portfolio vs tax income

- **Portfolio** column = passive income only: fund dividends, rental, SS, pension, consulting. **Not** account withdrawals.
- **Tax inc** is broader: includes IRA withdrawals, Roth conversions, taxable sale gains, taxable SS portion.

### Taxable withdrawal basis (important bug fix)

When selling from taxable brokerage, only the **gain** is income — not the full withdrawal.

- `taxable_cost_basis_ratio` = basis / market value (default 0.8; Fidelity import computes from cost basis on taxable accounts).
- **Wd basis** = Tax w/d × basis ratio → not taxed.
- **Wd gain** = Tax w/d × (1 − basis ratio) → stacks on LTCG.

### Net portfolio income (Phase 2a)

When enabled (default on): `withdrawal_need = spending − portfolio_income − RMD`. Spending is covered by passive income first before pulling from accounts.

### Withdrawal order (`engine/simulator.py`)

| Phase | Order |
|-------|--------|
| Early retirement (→65) | Taxable → Trad → Roth → Cash |
| Golden years (66–69) | Trad → Taxable → Roth |
| RMD years | RMD from Trad first (mandatory) |

### Return scenarios & Monte Carlo

- **Stress paths**: `base`, `bad_early`, `flat_low` via `engine/returns/scenarios.py`.
- **Monte Carlo**: 500 paths, normal returns (mean = `return_rate`, vol = `return_volatility`, clipped ±50%). Success = no year with `unfunded_spending >= $1`.

### Fidelity CSV import

- Parser: `engine/import_/fidelity.py`
- API: `POST /api/import/fidelity` (requires `python-multipart`)
- Maps account names: Individual/Joint → taxable; 401k/Rollover IRA → traditional; ROTH IRA → roth; FDRXX/FCASH sweeps → cash
- **Never paste broker CSVs in Cursor chat** — use in-app import only.

## Simulation table: tax columns

| Column | Meaning |
|--------|---------|
| **Wd need** | Spend − Portfolio − RMD (net pull from accounts) |
| **Wd basis** | Non-taxable return of principal from taxable sales |
| **Wd gain** | Taxable capital gain from taxable sales |
| **Ordinary** | Rental, pension, consulting, non-Q divs, IRA w/d, Roth conv, taxable SS |
| **LTCG inc** | Qualified divs + Wd gain |
| **AGI** | Ordinary + LTCG inc |
| **Deduct** | Standard + age 65+ + senior deductions |
| **Tax inc** | Taxable income after stacking (ordinary taxable + LTCG) |
| **Fed** | Ordinary tax + LTCG tax + NIIT |

Tax stacking: deductions reduce ordinary first; leftover can offset LTCG. Not simply AGI − Deduct.

## Privacy when using Cursor

- Enable **Privacy Mode** (ZDR with model providers).
- `.cursorignore` blocks `outlast.db`, `.env`, and `Portfolio_Positions*` CSV patterns.
- Delete chats that contained broker exports; run **Developer: GC Agent KV Blobs**.
- Reference this file in new chats: `@docs/PROJECT_CONTEXT.md`

## Key files

| Area | Path |
|------|------|
| Simulator | `engine/simulator.py` |
| Tax stacking | `engine/calculations/tax.py` |
| Monte Carlo | `engine/monte_carlo.py` |
| Fidelity import | `engine/import_/fidelity.py` |
| Profile model | `engine/models/profile.py` |
| API | `api/routes/profiles.py`, `api/routes/import_.py` |
| UI table | `web/src/components/SimulationTable.tsx` |
| Fidelity UI | `web/src/components/FidelityImport.tsx` |

## Not yet built (ideas from planning)

- Holdings panel / lot-level basis for tax-efficient sales
- Cash-before-IRA withdrawal ordering option
- MC: correlated returns, asset-class split, legacy floor success criterion
- PTC / AGI targeting solver

## Run

```bash
./scripts/dev.sh
# API :8888, web :5173
PYTHONPATH=. pytest
```
