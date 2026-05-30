from pathlib import Path

from engine.import_.fidelity import AccountBucket, parse_fidelity_csv

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "fidelity_sample.csv"


def test_parse_fidelity_sample_buckets():
    result = parse_fidelity_csv(FIXTURE.read_text())
    assert result.as_of == "Jan-01-2026 12:00 p.m ET"
    assert result.position_count == 6
    assert result.traditional_ira == 600_000.0  # 500k + 100k (sweep excluded)
    assert result.roth_ira == 50_000.0
    assert result.taxable == 25_000.0
    assert result.cash == 700.0  # 500 + 200 sweeps
    assert result.total_value == 675_700.0
    assert result.taxable_cost_basis_ratio == 0.8  # 20k basis / 25k value


def test_classifies_account_types():
    result = parse_fidelity_csv(FIXTURE.read_text())
    buckets = {a.account_name: a.bucket for a in result.accounts}
    assert buckets["Individual - TOD"] == AccountBucket.TAXABLE
    assert buckets["Rollover IRA"] == AccountBucket.TRADITIONAL_IRA
    assert buckets["ROTH IRA"] == AccountBucket.ROTH_IRA
    assert buckets["Self-Employed 401K"] == AccountBucket.TRADITIONAL_IRA
