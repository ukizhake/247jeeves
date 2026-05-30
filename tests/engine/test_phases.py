from engine.phases.detect import RetirementPhase, detect_phase


def test_phase_boundaries_match_richer_retirement():
    assert detect_phase(58) == RetirementPhase.EARLY_RETIREMENT
    assert detect_phase(65) == RetirementPhase.EARLY_RETIREMENT
    assert detect_phase(66) == RetirementPhase.GOLDEN_YEARS
    assert detect_phase(69) == RetirementPhase.GOLDEN_YEARS
    assert detect_phase(70) == RetirementPhase.PRE_RMD
    assert detect_phase(74) == RetirementPhase.PRE_RMD
    assert detect_phase(75) == RetirementPhase.RMD_YEARS
