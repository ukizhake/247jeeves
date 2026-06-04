"""Phase 3e: Shiller CAPE and SAFEMAX education."""

from engine.models.profile import FilingStatus, Profile
from engine.withdrawals.safemax import (
    UNIVERSAL_RULE_PCT,
    _interpolate_safemax,
    _load_anchors,
    compute_safemax_report,
    estimate_safemax_rate,
    resolve_cape,
)


def _profile(**kwargs) -> Profile:
    defaults = dict(
        name="safemax",
        age=65,
        plan_to_age=95,
        filing_status=FilingStatus.SINGLE,
        accounts={"traditional_ira": 800_000, "roth_ira": 100_000, "taxable": 600_000, "cash": 100_000},
        income={"dividends": 20_000},
        annual_spending=100_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        return_rate=0.06,
        return_volatility=0.12,
        inflation_rate=0.03,
    )
    defaults.update(kwargs)
    return Profile(**defaults)


def test_interpolate_between_deck_anchors():
    anchors = _load_anchors()
    mid = _interpolate_safemax(18.0, anchors)
    assert 0.05 < mid < 0.11


def test_high_cape_lowers_estimate():
    low = estimate_safemax_rate(_profile(shiller_cape=10.0))[0]
    high = estimate_safemax_rate(_profile(shiller_cape=30.0))[0]
    assert high < low


def test_high_inflation_regime_reduces_rate():
    normal = estimate_safemax_rate(_profile(shiller_cape=20.0, inflation_regime="normal"))[0]
    stressed = estimate_safemax_rate(_profile(shiller_cape=20.0, inflation_regime="high"))[0]
    assert stressed < normal


def test_resolve_cape_uses_profile_or_default():
    assert resolve_cape(_profile(shiller_cape=22.0))[1] == "profile"
    cape, src = resolve_cape(_profile())
    assert src == "default_assumption"
    assert cape > 20


def test_safemax_report_includes_universal_rule_and_mc():
    report = compute_safemax_report(_profile(shiller_cape=25.0), run_mc_validation=True, mc_paths=80)
    assert report.universal_rule_pct == UNIVERSAL_RULE_PCT
    assert report.estimated_safemax_pct >= 0.04
    assert len(report.nearby_anchors) >= 1
    assert report.mc_success_at_current_spending is not None
    assert report.mc_paths == 80
