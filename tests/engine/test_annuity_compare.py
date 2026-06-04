"""Phase 3d: insurance SPIA vs book FA."""

from engine.monte_carlo import MonteCarloConfig, run_annuity_comparison
from engine.models.profile import FilingStatus, Profile, ScenarioOverrides
from engine.withdrawals.annuity import apply_spira_premium, compute_annuity_education
from engine.withdrawals.spending import WithdrawalScheme, spending_for_year


def _profile(**kwargs) -> Profile:
    defaults = dict(
        name="annuity",
        age=65,
        plan_to_age=90,
        filing_status=FilingStatus.SINGLE,
        accounts={"traditional_ira": 800_000, "roth_ira": 100_000, "taxable": 600_000, "cash": 100_000},
        income={"dividends": 20_000, "rental": 0},
        annual_spending=100_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        return_rate=0.06,
        return_volatility=0.12,
        inflation_rate=0.03,
    )
    defaults.update(kwargs)
    return Profile(**defaults)


def test_apply_spira_reduces_wealth_and_sets_payout():
    p = _profile(spira_premium_paid=300_000, spira_payout_rate=0.06, annuity_income_annual=0)
    adjusted = apply_spira_premium(p)
    assert adjusted.annuity_income_annual == 18_000
    wealth = sum(adjusted.accounts.model_dump().values())
    assert wealth == 1_600_000 - 300_000


def test_book_fa_vs_spira_education_snapshots():
    p = _profile(spira_premium_paid=200_000, annuity_income_annual=12_000)
    edu = compute_annuity_education(p)
    assert len(edu.year_one_snapshots) >= 3
    book = next(s for s in edu.year_one_snapshots if s.variant == "book_fa")
    assert book.annuity_income == 0
    assert book.withdrawal_scheme == "fixed_annuity"


def test_floor_ceiling_caps_fp_swings():
    p = _profile(
        withdrawal_scheme=WithdrawalScheme.FLOOR_CEILING.value,
        initial_withdrawal_rate=0.10,
        floor_ceiling_cut_pct=0.05,
        floor_ceiling_raise_pct=0.05,
    )
    low, note = spending_for_year(
        p, 2, base_annual=100_000, prior_spending=100_000, prior_year_return=-0.3, wealth_start=500_000
    )
    assert low == 95_000
    assert "F&C" in note


def test_annuity_monte_carlo_compare_includes_spira_when_premium_set():
    p = _profile(spira_premium_paid=250_000)
    result = run_annuity_comparison(
        p,
        ScenarioOverrides(horizon_years=8, roth_conversion_annual=0),
        MonteCarloConfig(num_paths=40, seed=3),
    )
    keys = {v.variant for v in result.variants}
    assert keys == {"current", "book_fa", "spira"}
