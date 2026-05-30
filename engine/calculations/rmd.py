from engine.facts.loader import load_tax_config
from engine.facts.rmd_tables import rmd_divisor


def rmd_start_age() -> int:
    return int(load_tax_config().get("rmd_start_age", 75))


def compute_rmd(age: int, traditional_balance: float) -> float:
    if age < rmd_start_age() or traditional_balance <= 0:
        return 0.0
    divisor = rmd_divisor(age)
    if divisor <= 0:
        return 0.0
    return traditional_balance / divisor
