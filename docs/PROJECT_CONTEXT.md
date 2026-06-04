# Project context (sanitized)

Engineering decisions and mental model for outlast.money. **No personal portfolio data** — safe to keep in repo and reference in new Cursor chats.

## What this app is

Local-first retirement tax simulator. Four account buckets only: Traditional IRA, Roth IRA, taxable brokerage, cash. Rules engine recommends tactics from Richer Retirement-style YAML rules. Data stays in local SQLite (`outlast.db`, gitignored).

## Phase roadmap

### Phase 1 — Rules-based simulator (done)

Deterministic year-by-year projection, federal tax stacking, ~45 YAML rules, profile persistence, stress-free fixed 6% returns.

### Phase 2a — Realistic deterministic path (done)

- Net portfolio income: `Wd need = Spend − Portfolio − RMD`
- Return rate & inflation in UI
- Stress scenarios: `base`, `bad_early`, `flat_low`
- Fidelity CSV import → account buckets + cost basis ratio

### Phase 2b — Monte Carlo v1 (done)

- 500 random return paths through the same tax engine
- Success rate, median / p10 / p90 final wealth, fan chart
- `return_volatility` on profile (default 15%)

### Phase 2c — Strategy comparison (done)

Same random return paths, multiple **withdrawal policies**:

| Policy | Order |
|--------|--------|
| `phase_default` | Early: taxable→IRA→Roth→cash; golden: IRA→taxable→Roth |
| `taxable_first` | Taxable → IRA → Roth → cash (all phases) |
| `cash_first` | Cash → taxable → IRA → Roth |
| `ira_first` | IRA → taxable → Roth → cash (all phases) |

API: `POST /api/profiles/{id}/strategy-compare`  
UI: **Compare withdrawal strategies** button

### Phase 3a — COLA, annuity floor, annual review (done)

Combines lifestyle spending paths with guaranteed income and an October-style review ritual:

| Scheme | Behavior |
|--------|----------|
| `cola` | Prior spend × (1 + COLA rate) every year |
| `fixed_annuity` | Same nominal spending every year (book FA) |
| `performance_cola` | COLA unless prior year return &lt; 0 → hold flat; optional raise/cut caps |

- **COLA rate**: `spending_cola_rate` or defaults to `inflation_rate`
- **Annuity floor**: `annuity_income_annual` (+ optional `annuity_cola_rate`) subtracted from portfolio withdrawals
- **Annual review**: `annual_review_month` (default **10** = October); `POST /api/profiles/{id}/annual-review` with optional `prior_year_return`
- Simulator: `Wd need = Spend − Portfolio − Annuity − RMD`; year table shows **Annuity**, **IWR**, spending notes

Code: `engine/withdrawals/spending.py`, `engine/annual_review.py`  
UI: profile fields + **Run annual review** + **Apply recommended spending**

### Phase 3b — Target allocation & rebalance report (done)

Deck-style **55% stocks / 40% bonds / 5% cash** (five stock classes @ 11% each in the book; modeled as one stock sleeve here).

- **Target mix** on profile (`target_allocation`, default 55/40/5)
- **Current mix** optional (`current_allocation`); if omitted, cash % inferred from cash accounts, remainder split like target
- **Drift band** `rebalance_band_pct` (default 2%) — no trades if all sleeves within band
- **Report**: dollar drift per sleeve, buy/sell trades, prefer **IRA/Roth** (Principle 5 / rule `13_rebalance_tax_advantaged`)
- API: `POST /api/profiles/{id}/rebalance-report`
- UI: allocation fields + **Rebalance report** button

Code: `engine/allocation/rebalance.py`, `engine/models/allocation.py`

### Phase 3c — Spending schemes everywhere (done)

All deck-style **spending** paths on the simulator, annual review, Monte Carlo, and UI:

| Scheme | Behavior |
|--------|----------|
| `cola` | Year-one spend × inflation each year |
| `fixed_annuity` | Same nominal spending (FA) |
| `performance_cola` | COLA with hold-flat after down year (default) |
| `fixed_percentage` | `initial_withdrawal_rate` × start-of-year wealth (FP) |

- **Scenario override**: `spending_scheme_override` on `ScenarioOverrides` for one-off runs
- **Compare**: `POST /api/profiles/{id}/spending-compare` — same MC paths, four schemes (success, wealth, lifetime spending, tax)
- **Account order** (Phase 2c) renamed in UI to “Compare account withdrawal order” vs spending schemes
- Year table: **Spend rule** column when notes present; simulation badge shows active scheme

Code: `engine/withdrawals/spending.py`, `run_spending_scheme_comparison` in `engine/monte_carlo.py`

### Phase 3d — Insurance annuity vs book FA (done)

Clarifies two different “annuity” ideas from [A Richer Retirement withdrawals deck](https://docs.google.com/presentation/d/1S_luuPOwilH2mu9QwGQLPDzR3CYHmAtBHu3pNJS-DAo/edit?usp=sharing):

| Concept | Model |
|---------|--------|
| **Book FA** | `withdrawal_scheme=fixed_annuity` — nominal lifestyle spending from portfolio (not insurance) |
| **SPIA / pension** | `annuity_income_annual` offsets withdrawals; optional `spira_premium_paid` reduces investable balances in comparisons |
| **Floor & ceiling (F&C)** | Fifth spending scheme: FP % capped vs prior year (`floor_ceiling_raise_pct` / `floor_ceiling_cut_pct`, default ±10%) |

- Profile: `annuity_product_type`, `spira_premium_paid`, `spira_payout_rate`
- API: `POST /api/profiles/{id}/annuity-compare` — year-one snapshots + MC variants (current, book FA only, SPIA if premium set)
- UI: **Annuity vs book FA** button + SPIA fields in profile form
- Spending compare now includes **5 schemes** (adds F&C)

Code: `engine/withdrawals/annuity.py`, `run_annuity_comparison` in `engine/monte_carlo.py`

### Phase 3e — CAPE / SAFEMAX education (done)

Educational link between **Shiller CAPE** and **personal SAFEMAX** from [A Richer Retirement withdrawals deck](https://docs.google.com/presentation/d/1S_luuPOwilH2mu9QwGQLPDzR3CYHmAtBHu3pNJS-DAo/edit?usp=sharing):

- **SAFEMAX** = max initial withdrawal rate that sustained a 30-year path for that historical retiree (not the universal 4.7% worst case)
- **CAPE anchors** in `engine/withdrawals/data/cape_safemax_anchors.json` — piecewise interpolation + horizon / inflation adjustments
- Profile: `shiller_cape` (optional), `inflation_regime` (`normal` | `high`)
- API: `POST /api/profiles/{id}/safemax-report` — estimate vs universal 4.7%, implied IWR, deck anchor table, optional MC validation (200 paths)
- UI: **CAPE / SAFEMAX report** button + CAPE fields in profile form

Code: `engine/withdrawals/safemax.py`

### Phase 2d — Richer returns (next)

- 60/40 or equity/bond split with correlation
- Block bootstrap from historical series
- Legacy floor success criterion (“95% leave ≥ $X at age 90”)

### Phase 2e — Tax optimization solvers (next)

- Roth conversion solver (target bracket)
- PTC / MAGI band solver (ACA ages 59–64)
- IRMAA guardrails pre-Medicare

### Phase 2f — Holdings & basis (next)

- Holdings panel from Fidelity import
- High-basis-first lot sales (rule `08` becomes math)

### Phase 2g — Product polish

- Load / list saved plans in UI
- Side-by-side Roth scenario compare
- Export year table to CSV

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

When enabled (default on): `withdrawal_need = spending − portfolio_income − annuity_income − RMD`. Spending is covered by passive income and annuity floor first before pulling from accounts.

### Withdrawal order (`engine/withdrawals/policy.py`)

See Phase 2c table above. Configurable via `ScenarioOverrides.withdrawal_policy`.

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
| **Wd need** | Spend − Portfolio − Annuity − RMD (net pull from accounts) |
| **Annuity** | Guaranteed floor income offsetting withdrawals |
| **IWR** | Wd need ÷ wealth at start of year |
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
| Withdrawal policies | `engine/withdrawals/policy.py` |
| Tax stacking | `engine/calculations/tax.py` |
| Monte Carlo + strategy compare | `engine/monte_carlo.py` |
| Fidelity import | `engine/import_/fidelity.py` |
| Profile model | `engine/models/profile.py` |
| API | `api/routes/profiles.py`, `api/routes/import_.py` |
| UI table | `web/src/components/SimulationTable.tsx` |
| Strategy compare UI | `web/src/components/StrategyComparison.tsx` |
| Rebalance report | `engine/allocation/rebalance.py`, `web/src/components/RebalanceReport.tsx` |
| Annuity vs book FA | `engine/withdrawals/annuity.py`, `web/src/components/AnnuityComparison.tsx` |
| Fidelity UI | `web/src/components/FidelityImport.tsx` |

## Run

```bash
./scripts/dev.sh
# API :8888, web :5173
PYTHONPATH=. pytest
```
