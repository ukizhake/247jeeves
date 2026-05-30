from pathlib import Path
from typing import Any

import yaml

from engine.calculations.tax import bracket_top_for_rate
from engine.models.profile import FilingStatus, Profile, ScenarioOverrides
from engine.models.simulation import ActionRecommendation, Recommendation, SimulationResult, YearState
from engine.phases.detect import RetirementPhase

RULES_DIR = Path(__file__).parent / "data"
SOURCE = "richer_retirement"  # Google Slides framework


def _load_rules() -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    if not RULES_DIR.exists():
        return rules
    for path in sorted(RULES_DIR.glob("*.yaml")):
        with path.open() as f:
            doc = yaml.safe_load(f)
            if doc:
                rules.append(doc)
    return rules


def _ctx(
    profile: Profile,
    scenario: ScenarioOverrides,
    result: SimulationResult,
) -> dict[str, Any]:
    current = result.years[0] if result.years else None
    age_75_year = next((y for y in result.years if y.age == 75), None)
    return {
        "profile": profile,
        "scenario": scenario,
        "current": current,
        "rmd_at_75": age_75_year.rmd_required if age_75_year else 0,
        "ira_at_75": age_75_year.traditional_ira if age_75_year else 0,
        "spending": scenario.spending_override or profile.annual_spending,
    }


def bracket_top_for_low_income(filing_status: FilingStatus) -> float:
    return bracket_top_for_rate(0.22, filing_status)


def _eval_condition(name: str, ctx: dict[str, Any]) -> bool:
    profile: Profile = ctx["profile"]
    current: YearState | None = ctx["current"]

    if current is None:
        return False

    age = current.age
    phase = current.phase

    if name == "low_income":
        return current.taxable_income < bracket_top_for_low_income(profile.filing_status)
    if name == "before_rmd":
        return age < 75
    if name == "before_ss":
        return current.social_security <= 0
    if name == "traditional_ira_balance_gt":
        return current.traditional_ira > 500_000
    if name == "phase_early_retirement":
        return phase == RetirementPhase.EARLY_RETIREMENT.value
    if name == "phase_golden_years":
        return phase == RetirementPhase.GOLDEN_YEARS.value
    if name == "phase_pre_rmd":
        return phase == RetirementPhase.PRE_RMD.value
    if name == "phase_rmd_years":
        return phase == RetirementPhase.RMD_YEARS.value
    if name == "projected_rmd_gt_spending":
        return ctx["rmd_at_75"] > ctx["spending"] * 1.2
    if name == "bracket_room_22_gt":
        return current.bracket_room_22 > 10_000
    if name == "bracket_room_24_available":
        return current.bracket_room_24 > 5_000
    if name == "near_24_bracket":
        return current.marginal_rate >= 0.24 or current.bracket_room_24 < 12_000
    if name == "age_lt_65":
        return age < 65
    if name == "age_ge_66":
        return age >= 66
    if name == "age_ge_70":
        return age >= 70
    if name == "has_taxable_balance":
        return current.taxable > ctx["spending"] * 0.25
    if name == "has_traditional_ira":
        return current.traditional_ira > 50_000
    if name == "has_roth_balance":
        return current.roth_ira > 10_000
    if name == "rmd_exceeds_spending":
        return current.rmd_required > ctx["spending"] * 0.5
    if name == "has_tax_free_conversion_room":
        # Pre-conversion ordinary income (YearState.ordinary_income includes roth_conversion)
        pre_conv_ordinary = max(0.0, current.ordinary_income - current.roth_conversion)
        return (current.total_deductions - pre_conv_ordinary) > 5_000
    if name == "ltcg_tax_positive":
        return current.ltcg_tax > 0
    if name == "near_22_bracket":
        return current.marginal_rate >= 0.22 or current.bracket_room_22 < 12_000
    if name == "under_medicare":
        return age < 65
    if name == "aca_warning":
        return bool(current.aca_cliff_warning)
    if name == "has_spouse":
        return profile.spouse_age is not None
    if name == "spouse_older":
        return profile.spouse_age is not None and profile.spouse_age > profile.age
    if name == "age_lt_59":
        return age < 59
    if name == "age_55_to_59":
        return 55 <= age < 60
    if name == "taxable_nearly_depleted":
        return current.taxable < ctx["spending"] * 2
    if name == "has_rental_income":
        return profile.income.rental > 0 or current.rental_income > 0
    if name == "ltcg_room_available":
        return current.ltcg_tax == 0 and current.bracket_room_22 > 5_000
    if name == "high_traditional_ratio":
        trad = current.traditional_ira
        total = trad + current.roth_ira + current.taxable + current.cash
        return total > 0 and trad / total > 0.6
    return False


def _suggested_conversion(current: YearState, scenario: ScenarioOverrides) -> float:
    room = min(current.bracket_room_22, current.traditional_ira * 0.15)
    return max(0.0, round(room, -2))


def _tax_free_conversion_room(current: YearState) -> float:
    """Room to convert while staying within deductions (Principle 3)."""
    pre_conv_ordinary = max(0.0, current.ordinary_income - current.roth_conversion)
    return max(0.0, current.total_deductions - pre_conv_ordinary)


def _build_recommendation(rule: dict[str, Any], ctx: dict[str, Any]) -> Recommendation | None:
    current: YearState | None = ctx["current"]
    scenario: ScenarioOverrides = ctx["scenario"]
    if current is None:
        return None

    actions: list[ActionRecommendation] = []
    for action in rule.get("actions", []):
        if action == "recommend_roth_conversion":
            amount = scenario.roth_conversion_annual
            if amount is None:
                amount = _suggested_conversion(current, scenario)
            if amount and amount > 0:
                actions.append(
                    ActionRecommendation(
                        type="roth_convert",
                        amount=amount,
                        note=f"Fill toward {int(scenario.target_bracket_rate * 100)}% bracket",
                    )
                )
        elif action == "recommend_roth_conversion_tax_free":
            amount = scenario.roth_conversion_annual
            if amount is None:
                amount = min(_tax_free_conversion_room(current), current.traditional_ira)
                amount = round(max(0.0, amount), -2)
            if amount and amount > 0:
                actions.append(
                    ActionRecommendation(
                        type="roth_convert",
                        amount=amount,
                        note="Target tax-free conversion room (deductions shelter ordinary income)",
                    )
                )
        elif action == "recommend_withdraw_taxable":
            spend = ctx["spending"]
            actions.append(
                ActionRecommendation(
                    type="withdraw",
                    account="taxable",
                    amount=min(spend * 0.4, current.taxable),
                    note="Taxable first — capital gains stack on ordinary income (Ch. 10)",
                )
            )
        elif action == "recommend_withdraw_traditional":
            spend = ctx["spending"]
            actions.append(
                ActionRecommendation(
                    type="withdraw",
                    account="traditional",
                    amount=min(spend * 0.5, current.traditional_ira),
                    note="Golden years: fund spending from pre-tax accounts (slide 41)",
                )
            )
        elif action == "recommend_withdraw_roth":
            actions.append(
                ActionRecommendation(
                    type="withdraw",
                    account="roth",
                    amount=min(12_000, current.roth_ira),
                    note="Use Roth instead of IRA to avoid 24% bracket (slide 29)",
                )
            )
        elif action == "recommend_delay_ss":
            actions.append(
                ActionRecommendation(
                    type="delay_social_security",
                    note="Claim Social Security at 70 when possible (slide 40)",
                )
            )
        elif action == "recommend_income_layering":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Layer income: Roth/cash (no MAGI) → taxable LTCG → minimal pre-tax (slide 35)",
                )
            )
        elif action == "recommend_asset_location_bonds_ira":
            actions.append(
                ActionRecommendation(
                    type="asset_location",
                    note="Hold bonds in IRA/401(k); keep tax-efficient equity in taxable (slides 17, 45)",
                )
            )
        elif action == "recommend_asset_location_equity_taxable":
            actions.append(
                ActionRecommendation(
                    type="asset_location",
                    note="Index equity in taxable; harvest 0% LTCG room when income is low (slide 62)",
                )
            )
        elif action == "recommend_qcd":
            actions.append(
                ActionRecommendation(
                    type="qcd",
                    note="Qualified Charitable Distributions reduce RMDs and taxable income (slide 42)",
                )
            )
        elif action == "recommend_hidden_roth_ira":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="IRA withdrawals may be offset by standard + senior deductions ('Hidden Roth IRA', slide 42)",
                )
            )
        elif action == "caution_roth_conversion_post_70":
            actions.append(
                ActionRecommendation(
                    type="warn",
                    note="After 70, Roth conversions are often less attractive — compare to future RMD taxes (slide 42)",
                )
            )
        elif action == "recommend_0pct_ltcg_harvest":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Realize long-term gains in the 0% LTCG bracket while taxable income is low (slide 62)",
                )
            )
        elif action == "warn_future_rmd_shock":
            actions.append(
                ActionRecommendation(
                    type="warn",
                    note=f"Projected RMD at 75: ${ctx['rmd_at_75']:,.0f}",
                )
            )
        elif action == "warn_widow_trap":
            actions.append(
                ActionRecommendation(
                    type="warn",
                    note="Surviving spouse MFJ→Single compresses brackets; Roth can reduce SS taxation (slide 31)",
                )
            )
        elif action == "warn_irmaa":
            actions.append(
                ActionRecommendation(
                    type="warn",
                    note="Manage MAGI to avoid IRMAA Medicare surcharges (slide 27)",
                )
            )
        elif action == "warn_aca_cliff":
            actions.append(
                ActionRecommendation(
                    type="warn",
                    note="Keep MAGI low for Premium Tax Credit if on ACA before 65 (slides 11, 34)",
                )
            )
        elif action == "recommend_tactical_roth_to_avoid_bracket":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="If you're near a bracket edge or 0% LTCG limit, consider a tactical Roth withdrawal for the last dollars (Principle 7).",
                )
            )
        elif action == "warn_roth_conversion_pushes_ltcg_15":
            actions.append(
                ActionRecommendation(
                    type="warn",
                    note="Roth conversions can push QDI/LTCG into the 15% bracket — compare tradeoffs (Principle 3 caveat).",
                )
            )
        elif action == "recommend_specific_id_high_basis":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="When selling taxable lots, consider specific ID and high-basis lots first to reduce realized gains (slide 42).",
                )
            )
        elif action == "recommend_blended_distributions_for_ptc":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="If optimizing ACA Premium Tax Credit, blend taxable + traditional + Roth to smooth MAGI (Principle 8).",
                )
            )
        elif action == "recommend_older_spouse_ira_first":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Draw from the older spouse's traditional IRA/401(k) first — they hit RMDs sooner (Principle 4).",
                )
            )
        elif action == "recommend_rebalance_tax_advantaged":
            actions.append(
                ActionRecommendation(
                    type="asset_location",
                    note="Rebalance inside IRAs/Roth, not taxable — avoids realizing gains (Principle 5).",
                )
            )
        elif action == "recommend_hsa_puqme":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="HSA PUQME reimbursements and Medicare premiums are tax-free; use tactically to keep MAGI low (Principle 7).",
                )
            )
        elif action == "recommend_72t_sepp":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="72(t) SEPP can fund early retirement from IRA without 10% penalty when taxable assets run out (Ch. 12).",
                )
            )
        elif action == "recommend_rule_of_55":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Rule of 55: penalty-free 401(k) distributions after separating from employer in year you turn 55+ (Ch. 12).",
                )
            )
        elif action == "recommend_roth_401k_rollover":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Roll Roth 401(k) to Roth IRA before 59½ — IRA ordering rules access contributions tax-free (Ch. 12).",
                )
            )
        elif action == "caution_roth_conversion_rmd_years":
            actions.append(
                ActionRecommendation(
                    type="warn",
                    note="After RMDs begin, Roth conversions stack on RMD/SS income — satisfy RMD first; conversions rarely help (slide 63).",
                )
            )
        elif action == "recommend_living_expenses_reduce_rmd":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Living expenses paid from traditional IRA reduce balance and future RMDs — don't fear spending pre-tax (slides 88–90).",
                )
            )
        elif action == "recommend_tax_loss_harvest":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Harvest losses in taxable accounts to offset gains and lower MAGI for PTC (Ch. 23).",
                )
            )
        elif action == "recommend_tax_gain_harvest":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Realize gains in the 0% LTCG bracket to reset basis — tax-free step-up in cost basis (Ch. 24).",
                )
            )
        elif action == "recommend_rental_in_taxable":
            actions.append(
                ActionRecommendation(
                    type="asset_location",
                    note="Hold rental real estate in taxable/rev trust, not self-directed IRA — depreciation shelter + step-up at death (Ch. 26).",
                )
            )
        elif action == "recommend_inherited_ira_strategy":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Before 59½, keep spouse IRA as inherited IRA for penalty-free access; roll to own IRA after 59½ (Ch. 12).",
                )
            )
        elif action == "recommend_bronze_hsa":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Bronze ACA plan qualifies as HDHP — HSA contributions lower MAGI and boost PTC ('bronze is gold', Ch. 13).",
                )
            )
        elif action == "recommend_goldilocks_ptc":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Goldilocks PTC: taxable (basis-heavy) + modest Roth conversions — not all-Roth (too low) or all-IRA (too high) (slide 97).",
                )
            )
        elif action == "recommend_domestic_equity_taxable":
            actions.append(
                ActionRecommendation(
                    type="asset_location",
                    note="Domestic equity index funds in taxable — low yield, high QDI%; bonds/international better in IRA/Roth (slides 76, 95).",
                )
            )
        elif action == "recommend_sell_bonds_taxable_first":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Sell least tax-efficient taxable holdings (bonds, int'l) first; take dividends as cash vs reinvesting (slide 60).",
                )
            )
        elif action == "recommend_dividend_cash":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Direct fund dividends to cash to fund spending — fewer capital gain sales and lower MAGI (slide 60).",
                )
            )
        elif action == "recommend_sequence_returns_taxable":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Taxable-first drawdown defers taxes in bear markets — sequence-of-returns protection (slides 74, 100).",
                )
            )
        elif action == "recommend_keep_ordinary_income_low":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Keep ordinary income low — opens Roth conversions, PTC, and lower SS/RMD taxation (Principle 2).",
                )
            )
        elif action == "recommend_ira_withholding":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="IRA distribution withholding can pay federal tax without extra MAGI from estimated payments (Ch. 13).",
                )
            )
        elif action == "recommend_avoid_roth_withholding":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Avoid withholding on Roth conversions in early retirement — pay via estimated tax or IRA withholding instead (Ch. 13).",
                )
            )
        elif action == "recommend_rmd_perspective":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="RMDs are a small slice of retirement — effective rates often stay modest; QCDs and spending reduce balance (slides 88–90).",
                )
            )
        elif action == "recommend_backdoor_roth":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Above IRA deductibility limits? Backdoor Roth (nondeductible IRA → convert) — file Form 8606 (Ch. 9).",
                )
            )
        elif action == "recommend_mega_backdoor_roth":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Mega Backdoor Roth via after-tax 401(k) → in-plan Roth or in-service rollover builds large Roth basis (Ch. 9).",
                )
            )
        elif action == "recommend_457b_early_access":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Governmental 457(b): no 10% early penalty; can double deferrals with 401(k)/403(b) (Ch. 9).",
                )
            )
        elif action == "recommend_beneficiary_roth":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="Roth conversions can reduce heirs' tax on inherited IRAs — secondary to your own spending needs (Ch. 17).",
                )
            )
        elif action == "recommend_unneeded_rmd_tactics":
            actions.append(
                ActionRecommendation(
                    type="info",
                    note="RMD exceeds spending? QCD for charity, Roth withdrawals, or reinvest after-tax — don't force extra ordinary income (slide 63).",
                )
            )

    if not actions:
        return None

    rationale = rule.get("rationale", "")
    if rule.get("source"):
        rationale = f"{rationale} [{rule['source']}]".strip()

    return Recommendation(
        rule_id=rule.get("rule_name", "unknown"),
        priority=int(rule.get("priority", 50)),
        title=rule.get("title", rule.get("rule_name", "Recommendation")),
        phase=rule.get("phase", current.phase),
        actions=actions,
        tradeoffs=list(rule.get("tradeoffs", [])),
        rationale=rationale,
    )


def run_rules(
    profile: Profile,
    scenario: ScenarioOverrides,
    result: SimulationResult,
) -> list[Recommendation]:
    ctx = _ctx(profile, scenario, result)
    current: YearState | None = ctx["current"]
    if current is None:
        return []

    recs: list[Recommendation] = []
    for rule in _load_rules():
        phase = rule.get("phase")
        if phase and phase != current.phase:
            continue

        conditions = rule.get("conditions", [])
        if not all(_eval_condition(c, ctx) for c in conditions):
            continue

        rec = _build_recommendation(rule, ctx)
        if rec:
            recs.append(rec)

    if current.irmaa_warning:
        recs.append(
            Recommendation(
                rule_id="irmaa_proximity",
                priority=5,
                title="IRMAA proximity",
                phase=current.phase,
                actions=[
                    ActionRecommendation(
                        type="warn",
                        note="Projected MAGI within 10% of IRMAA threshold",
                    )
                ],
                tradeoffs=["Higher Medicare Part B/D premiums"],
                rationale="Richer Retirement Ch. 27 — IRMAA",
            )
        )
    if getattr(current, "niit_warning", False) and not any(r.rule_id == "niit_applies" for r in recs):
        recs.append(
            Recommendation(
                rule_id="niit_applies",
                priority=6,
                title="Net Investment Income Tax (NIIT)",
                phase=current.phase,
                actions=[
                    ActionRecommendation(
                        type="warn",
                        note="3.8% NIIT on investment income above MAGI threshold (Ch. 8)",
                    )
                ],
                tradeoffs=["Consider asset location and timing of capital gains"],
                rationale="Richer Retirement — Form 8960",
            )
        )
    if current.aca_cliff_warning:
        recs.append(
            Recommendation(
                rule_id="aca_cliff",
                priority=8,
                title="ACA / Premium Tax Credit",
                phase=current.phase,
                actions=[
                    ActionRecommendation(
                        type="warn",
                        note="MAGI near ACA subsidy cliff (under 65)",
                    )
                ],
                tradeoffs=["Loss of premium tax credit"],
                rationale="Richer Retirement — PTC optimization",
            )
        )

    recs.sort(key=lambda r: r.priority)
    return recs
