"""IRS Uniform Lifetime Table divisors (simplified subset)."""

# Age -> divisor for RMD calculation (balance / divisor)
UNIFORM_LIFETIME_DIVISORS: dict[int, float] = {
    75: 24.6,
    76: 23.7,
    77: 22.9,
    78: 22.0,
    79: 21.1,
    80: 20.2,
    81: 19.4,
    82: 18.5,
    83: 17.7,
    84: 16.8,
    85: 16.0,
    86: 15.2,
    87: 14.4,
    88: 13.7,
    89: 12.9,
    90: 12.2,
    91: 11.5,
    92: 10.8,
    93: 10.1,
    94: 9.5,
    95: 8.9,
}


def rmd_divisor(age: int) -> float:
    if age < 75:
        return 0.0
    if age in UNIFORM_LIFETIME_DIVISORS:
        return UNIFORM_LIFETIME_DIVISORS[age]
    return 8.9  # 95+
