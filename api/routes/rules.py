from pathlib import Path

import yaml
from fastapi import APIRouter

router = APIRouter(prefix="/rules", tags=["rules"])

RULES_DIR = Path(__file__).resolve().parents[2] / "engine" / "rules" / "data"


@router.get("")
def list_rules() -> list[dict]:
    rules = []
    if RULES_DIR.exists():
        for path in sorted(RULES_DIR.glob("*.yaml")):
            with path.open() as f:
                doc = yaml.safe_load(f)
                if doc:
                    rules.append(doc)
    return rules
