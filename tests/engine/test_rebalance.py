"""Phase 3b: target allocation and rebalance report."""

import pytest

from engine.allocation.rebalance import compute_rebalance_report
from engine.models.allocation import AssetAllocation
from engine.models.profile import FilingStatus, Profile


def _profile(**kwargs) -> Profile:
    defaults = dict(
        name="alloc",
        age=65,
        filing_status=FilingStatus.SINGLE,
        accounts={"traditional_ira": 600_000, "roth_ira": 200_000, "taxable": 400_000, "cash": 50_000},
        income={"dividends": 0, "rental": 0},
        annual_spending=80_000,
        social_security_claim_age=70,
        social_security_annual_at_claim=0,
        return_rate=0.06,
        inflation_rate=0.03,
    )
    defaults.update(kwargs)
    return Profile(**defaults)


def test_default_target_is_55_40_5():
    p = _profile()
    report = compute_rebalance_report(p)
    assert report.target.stocks == 0.55
    assert report.target.bonds == 0.40
    assert report.target.cash == 0.05
    assert report.total_wealth == 1_250_000


def test_drift_triggers_trades():
    p = _profile(
        current_allocation=AssetAllocation(stocks=0.70, bonds=0.25, cash=0.05),
        rebalance_band_pct=0.01,
    )
    report = compute_rebalance_report(p)
    assert report.needs_rebalance is True
    assert report.max_drift_pct >= 0.14
    stock_slice = next(s for s in report.slices if s.asset == "stocks")
    assert stock_slice.drift_dollars > 0
    assert any(t.asset == "stocks" and t.action == "sell" for t in report.trades)
    assert any(t.asset == "bonds" and t.action == "buy" for t in report.trades)


def test_within_band_no_trades():
    p = _profile(
        current_allocation=AssetAllocation(stocks=0.56, bonds=0.39, cash=0.05),
        rebalance_band_pct=0.02,
    )
    report = compute_rebalance_report(p)
    assert report.needs_rebalance is False
    assert report.trades == []


def test_allocation_must_sum_to_one():
    with pytest.raises(ValueError, match="100%"):
        AssetAllocation(stocks=0.5, bonds=0.3, cash=0.1)
