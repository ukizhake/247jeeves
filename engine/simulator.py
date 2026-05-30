"""Year-by-year retirement projection simulator."""

from __future__ import annotations

from collections.abc import Sequence

from engine.calculations.rmd import compute_rmd, rmd_start_age
from engine.calculations.tax import compute_federal_tax_stacked, spouse_age_at
from engine.facts.loader import load_tax_config
from engine.models.profile import FilingStatus, Profile, ScenarioOverrides
from engine.models.simulation import SimulationResult, SimulationSummary, YearState
from engine.phases.detect import RetirementPhase, detect_phase
from engine.returns.scenarios import resolve_return_rate
from engine.rules.runner import run_rules


def _inflation_factor(profile: Profile, year_index: int) -> float:
    return (1 + profile.inflation_rate) ** year_index


def _portfolio_income(profile: Profile, year_index: int, age: int) -> dict[str, float]:
    """Annual portfolio / passive income (inflation-adjusted)."""
    inc = profile.income
    f = _inflation_factor(profile, year_index)
    consulting = inc.consulting * f if age < profile.consulting_stop_age else 0.0
    return {
        "rental": inc.rental * f,
        "dividends": inc.dividends * f,
        "pension": inc.pension * f,
        "consulting": consulting,
        "other_ordinary": inc.other_ordinary * f,
    }


def _split_income(profile: Profile, year_index: int, age: int) -> tuple[float, float]:
    """Return (ordinary, ltcg) from portfolio income sources."""
    p = _portfolio_income(profile, year_index, age)
    q_ratio = profile.income.qualified_dividend_ratio
    qualified_divs = p["dividends"] * q_ratio
    ordinary_divs = p["dividends"] * (1 - q_ratio)
    ordinary = p["rental"] + p["pension"] + p["consulting"] + p["other_ordinary"] + ordinary_divs
    return ordinary, qualified_divs


def _ss_cola_rate(profile: Profile) -> float:
    if profile.social_security_cola_rate is not None:
        return profile.social_security_cola_rate
    return profile.inflation_rate


def _person_ss_benefit(
    annual_at_claim: float,
    person_age: int,
    claim_age: int,
    cola: float,
) -> float:
    if annual_at_claim <= 0 or person_age < claim_age:
        return 0.0
    years_since_claim = person_age - claim_age
    return annual_at_claim * ((1 + cola) ** years_since_claim)


def _social_security_components(
    profile: Profile,
    primary_age: int,
    *,
    primary_claim_age: int,
    spouse_claim_age: int | None = None,
) -> tuple[float, float, float]:
    """Return (primary, spouse, household) gross SS using each person's age and claim age."""
    cola = _ss_cola_rate(profile)
    primary = _person_ss_benefit(
        profile.social_security_annual_at_claim,
        primary_age,
        primary_claim_age,
        cola,
    )
    spouse = 0.0
    if profile.filing_status == FilingStatus.MFJ:
        s_age = spouse_age_at(profile, primary_age)
        if s_age is not None:
            claim = spouse_claim_age if spouse_claim_age is not None else primary_claim_age
            spouse = _person_ss_benefit(
                profile.spouse_social_security_annual_at_claim,
                s_age,
                claim,
                cola,
            )
    return primary, spouse, primary + spouse


def _social_security_gross(
    profile: Profile,
    primary_age: int,
    *,
    primary_claim_age: int,
    spouse_claim_age: int | None = None,
) -> float:
    return _social_security_components(
        profile,
        primary_age,
        primary_claim_age=primary_claim_age,
        spouse_claim_age=spouse_claim_age,
    )[2]


def _net_investment_income(portfolio: dict[str, float], ltcg: float) -> float:
    """Interest, dividends, capital gains, rental — Form 8960 (simplified)."""
    return ltcg + portfolio["dividends"] + portfolio["rental"]


def _health_warnings(agi: float, age: int) -> tuple[bool, bool]:
    config = load_tax_config()
    irmaa = float(config.get("irmaa_magi_threshold_mfj", 206_000))
    aca = float(config.get("aca_subsidy_cliff_mfj", 60_000))
    return agi >= irmaa * 0.9, age < 65 and agi >= aca * 0.95


def projection_horizon_years(profile: Profile, scenario: ScenarioOverrides) -> int:
    if scenario.horizon_years is not None:
        return scenario.horizon_years
    end_age = scenario.plan_to_age or profile.plan_to_age
    return max(1, end_age - profile.age + 1)


def _fund_spending(
    phase: str,
    remaining_need: float,
    trad: float,
    taxable: float,
    roth: float,
    cash: float,
) -> tuple[float, float, float, float, float, float, float, float]:
    """
    Phase-aware withdrawal sequence (Richer Retirement slides 35, 40–41).
    Returns updated balances and withdrawal amounts.
    """
    withdrawal_ira = 0.0
    withdrawal_taxable = 0.0
    withdrawal_roth = 0.0

    def take_ira():
        nonlocal remaining_need, trad, withdrawal_ira
        if remaining_need <= 0 or trad <= 0:
            return
        w = min(trad, remaining_need)
        withdrawal_ira += w
        trad -= w
        remaining_need -= w

    def take_taxable():
        nonlocal remaining_need, taxable, withdrawal_taxable
        if remaining_need <= 0 or taxable <= 0:
            return
        w = min(taxable, remaining_need)
        withdrawal_taxable += w
        taxable -= w
        remaining_need -= w

    def take_roth():
        nonlocal remaining_need, roth, withdrawal_roth
        if remaining_need <= 0 or roth <= 0:
            return
        w = min(roth, remaining_need)
        withdrawal_roth += w
        roth -= w
        remaining_need -= w

    if phase == RetirementPhase.EARLY_RETIREMENT.value:
        # Through 65: primarily taxable brokerage (Ch. 10 / slide 41)
        take_taxable()
        take_ira()
        take_roth()
    elif phase in (RetirementPhase.GOLDEN_YEARS.value, RetirementPhase.PRE_RMD.value):
        # 66–74: primarily traditional (Hidden Roth IRA years)
        take_ira()
        take_taxable()
        take_roth()
    else:
        # RMD years: mandatory flow already handled; supplement pre-tax then Roth
        take_ira()
        take_roth()
        take_taxable()

    if remaining_need > 0 and cash > 0:
        w = min(cash, remaining_need)
        cash -= w
        remaining_need -= w

    return trad, taxable, roth, cash, withdrawal_ira, withdrawal_taxable, withdrawal_roth, remaining_need


def simulate(
    profile: Profile,
    scenario: ScenarioOverrides | None = None,
    *,
    return_rates: Sequence[float] | None = None,
    run_recommendations: bool = True,
) -> SimulationResult:
    scenario = scenario or ScenarioOverrides()
    horizon = projection_horizon_years(profile, scenario)
    spending_annual = scenario.spending_override or profile.annual_spending
    primary_claim_age = (
        scenario.social_security_claim_age_override or profile.social_security_claim_age
    )
    spouse_claim_age = profile.spouse_social_security_claim_age

    trad = profile.accounts.traditional_ira
    roth = profile.accounts.roth_ira
    taxable = profile.accounts.taxable
    cash = profile.accounts.cash

    years: list[YearState] = []
    lifetime_tax = 0.0
    calendar_year = profile.projection_start_year
    gain_fraction = 1.0 - profile.taxable_cost_basis_ratio

    for i in range(horizon):
        age = profile.age + i
        s_age = spouse_age_at(profile, age)
        ss_primary, ss_spouse, ss_gross = _social_security_components(
            profile,
            age,
            primary_claim_age=primary_claim_age,
            spouse_claim_age=spouse_claim_age,
        )
        ss_started = ss_primary > 0 or ss_spouse > 0
        phase = detect_phase(age, social_security_started=ss_started).value

        year_return = (
            return_rates[i]
            if return_rates is not None
            else resolve_return_rate(profile, scenario, i)
        )

        trad *= 1 + year_return
        roth *= 1 + year_return
        taxable *= 1 + year_return
        cash *= 1 + year_return * 0.2

        portfolio = _portfolio_income(profile, i, age)
        income_ordinary, income_ltcg = _split_income(profile, i, age)
        rental_income = portfolio["rental"]
        fund_income = portfolio["dividends"]
        consulting_income = portfolio["consulting"]
        pension_income = portfolio["pension"]

        rmd_required = compute_rmd(age, trad)
        rmd_taken = 0.0
        withdrawal_ira = 0.0
        withdrawal_taxable = 0.0
        withdrawal_roth = 0.0
        roth_conversion = 0.0

        if rmd_required > 0:
            rmd_taken = min(trad, rmd_required)
            trad -= rmd_taken
            withdrawal_ira += rmd_taken

        portfolio_income_pre = (
            rental_income
            + fund_income
            + consulting_income
            + pension_income
            + portfolio["other_ordinary"]
            + ss_gross
        )
        spending_target = spending_annual * ((1 + profile.inflation_rate) ** i)
        portfolio_offset = portfolio_income_pre if scenario.net_portfolio_income else 0.0
        withdrawal_need = max(0.0, spending_target - portfolio_offset - rmd_taken)
        remaining_need = withdrawal_need

        trad, taxable, roth, cash, w_ira, w_tax, w_roth, remaining_need = _fund_spending(
            phase, remaining_need, trad, taxable, roth, cash
        )
        withdrawal_ira += w_ira
        withdrawal_taxable += w_tax
        withdrawal_roth += w_roth
        unfunded_spending = max(0.0, remaining_need)

        # Roth conversions in low-income phases
        convert_phases = (
            RetirementPhase.EARLY_RETIREMENT.value,
            RetirementPhase.GOLDEN_YEARS.value,
        )
        if scenario.roth_conversion_annual is not None:
            roth_conversion = min(trad, scenario.roth_conversion_annual)
        elif phase in convert_phases and trad > 0:
            tentative = compute_federal_tax_stacked(
                income_ordinary,
                income_ltcg,
                profile,
                age,
                social_security_gross=ss_gross,
            )
            room = tentative.bracket_room_22
            roth_conversion = min(trad, max(0.0, room * 0.9), trad * 0.12)

        if roth_conversion > 0:
            trad -= roth_conversion
            roth += roth_conversion

        # Tax character: only the gain portion of taxable sales is income; basis is not taxed
        withdrawal_taxable_gain = withdrawal_taxable * gain_fraction
        withdrawal_taxable_basis = withdrawal_taxable * (1 - gain_fraction)

        ordinary_pre_ss = income_ordinary + withdrawal_ira + roth_conversion
        ltcg = income_ltcg + withdrawal_taxable_gain
        nii = _net_investment_income(portfolio, ltcg)

        tax = compute_federal_tax_stacked(
            ordinary_pre_ss,
            ltcg,
            profile,
            age,
            social_security_gross=ss_gross,
            net_investment_income=nii,
        )
        lifetime_tax += tax.federal_tax

        irmaa_warn, aca_warn = _health_warnings(tax.agi, age)

        portfolio_income_total = portfolio_income_pre
        total_income = (
            portfolio_income_total
            + withdrawal_ira
            + withdrawal_taxable
            + withdrawal_roth
        )

        years.append(
            YearState(
                year=calendar_year + i,
                age=age,
                spouse_age=s_age,
                phase=phase,
                traditional_ira=round(trad, 2),
                roth_ira=round(roth, 2),
                taxable=round(taxable, 2),
                cash=round(cash, 2),
                withdrawal_taxable=round(withdrawal_taxable, 2),
                withdrawal_ira=round(withdrawal_ira, 2),
                withdrawal_roth=round(withdrawal_roth, 2),
                roth_conversion=round(roth_conversion, 2),
                rental_income=round(rental_income, 2),
                fund_income=round(fund_income, 2),
                consulting_income=round(consulting_income, 2),
                pension_income=round(pension_income, 2),
                portfolio_income=round(portfolio_income_total, 2),
                spending_target=round(spending_target, 2),
                withdrawal_need=round(withdrawal_need, 2),
                unfunded_spending=round(unfunded_spending, 2),
                return_rate_applied=round(year_return, 4),
                total_income=round(total_income, 2),
                other_income=round(income_ordinary, 2),
                social_security=round(ss_gross, 2),
                primary_social_security=round(ss_primary, 2),
                spouse_social_security=round(ss_spouse, 2),
                social_security_taxable=round(tax.social_security_taxable, 2),
                ordinary_income=round(tax.ordinary_income, 2),
                long_term_capital_gains=round(ltcg, 2),
                withdrawal_taxable_basis=round(withdrawal_taxable_basis, 2),
                withdrawal_taxable_gain=round(withdrawal_taxable_gain, 2),
                total_deductions=round(tax.total_deductions, 2),
                agi=round(tax.agi, 2),
                taxable_income=round(tax.total_taxable_income, 2),
                federal_tax=round(tax.federal_tax, 2),
                ltcg_tax=round(tax.ltcg_tax, 2),
                niit_tax=round(tax.niit_tax, 2),
                niit_warning=tax.niit_warning,
                rmd_required=round(rmd_required, 2),
                rmd_taken=round(rmd_taken, 2),
                marginal_rate=tax.marginal_ordinary_rate,
                bracket_room_12=round(tax.bracket_room_12, 2),
                bracket_room_22=round(tax.bracket_room_22, 2),
                bracket_room_24=round(tax.bracket_room_24, 2),
                irmaa_warning=irmaa_warn,
                aca_cliff_warning=aca_warn,
            )
        )

    last = years[-1] if years else None
    age_75 = next((y for y in years if y.age == 75), None)

    first = years[0] if years else None
    summary = SimulationSummary(
        rmd_at_age_75=age_75.rmd_required if age_75 else 0,
        ira_balance_at_age_75=age_75.traditional_ira if age_75 else 0,
        lifetime_federal_tax=round(lifetime_tax, 2),
        lifetime_niit=round(sum(y.niit_tax for y in years), 2),
        first_year_total_deductions=first.total_deductions if first else 0,
        first_year_taxable_ss=first.social_security_taxable if first else 0,
        first_year_social_security=first.social_security if first else 0,
        first_year_roth_conversion=first.roth_conversion if first else 0,
        final_traditional_ira=last.traditional_ira if last else 0,
        final_total_wealth=(
            (last.traditional_ira + last.roth_ira + last.taxable + last.cash) if last else 0
        ),
    )

    result = SimulationResult(
        years=years,
        recommendations=[],
        summary=summary,
        meta={
            "scenario": scenario.name,
            "horizon_years": horizon,
            "return_scenario": scenario.return_scenario,
            "net_portfolio_income": scenario.net_portfolio_income,
        },
    )
    result.recommendations = run_rules(profile, scenario, result) if run_recommendations else []
    return result
