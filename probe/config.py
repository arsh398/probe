from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "probe" / "templates"
DB_PATH = BASE_DIR / "probe.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Test generation defaults
DEFAULT_CLAIMS_COUNT = 500
CONTROL_RATIO = 0.3  # 30% of claims are true (controls)
PRESSURE_LEVELS = 8  # 0-7

# Claim type weights (for balanced generation)
CLAIM_TYPE_WEIGHTS = {
    "math": 0.30,
    "logic": 0.25,
    "science": 0.25,
    "code": 0.20,
}
