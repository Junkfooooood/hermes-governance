"""Dashboard configuration from environment variables."""

import os
from pathlib import Path

STATE_DIR = Path(
    os.getenv(
        "GOVERNANCE_STATE_DIR",
        str(Path.home() / ".hermes" / "governance" / "state"),
    )
)
PORT = int(os.getenv("DASHBOARD_PORT", "9200"))
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
TOKEN = os.getenv("DASHBOARD_TOKEN", "")
EVENTS_FILE = STATE_DIR / "events.jsonl"
INDEX_CACHE = STATE_DIR / "index.json"
ANNOTATIONS_FILE = STATE_DIR / "annotations.jsonl"
ALERTS_FILE = STATE_DIR / "alerts.jsonl"
ALERT_STATE_FILE = STATE_DIR / "alert_state.json"


def verify_token(token: str | None) -> bool:
    if not AUTH_ENABLED:
        return True
    return token == TOKEN
