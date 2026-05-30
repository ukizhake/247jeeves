from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@lru_cache
def load_tax_config() -> dict[str, Any]:
    path = DATA_DIR / "tax_brackets_2026.yaml"
    with path.open() as f:
        return yaml.safe_load(f)
