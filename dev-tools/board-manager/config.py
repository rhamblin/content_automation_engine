"""Config loader — reads JSON data file, validates boards, resolves credentials."""

import json
from dataclasses import dataclass
from pathlib import Path

from common.workflows.board_manager import BoardItem
from common.workflows.board_manager.board_manager_request import VALID_PRIVACY

CONFIG_ROOT = Path(__file__).parent.parent.parent / "config" / "tenants"


@dataclass(frozen=True)
class BoardManagerConfig:
    """Validated config from data file + tenant credentials."""

    tenant: str
    boards: list[BoardItem]
    access_token: str


def load_config(data_file: Path) -> BoardManagerConfig:
    """Load and validate data file, resolve credentials."""
    raw = json.loads(data_file.read_text())

    tenant = raw.get("tenant")
    if not tenant:
        raise ValueError("data file missing required field: tenant")

    boards_raw = raw.get("boards")
    if not boards_raw or not isinstance(boards_raw, list):
        raise ValueError("data file missing required field: boards (non-empty list)")

    boards: list[BoardItem] = []
    for entry in boards_raw:
        name = entry.get("name")
        if not name:
            raise ValueError("board missing required field: name")

        privacy = entry.get("privacy", "PUBLIC").upper()
        if privacy not in VALID_PRIVACY:
            raise ValueError(f"invalid privacy '{privacy}', must be one of {VALID_PRIVACY}")

        boards.append(BoardItem(name=name, privacy=privacy))

    # --- resolve credentials ---
    creds_path = CONFIG_ROOT / tenant / "credentials" / "pinterest.json"
    if not creds_path.exists():
        raise ValueError(f"credentials not found: {creds_path}")

    creds = json.loads(creds_path.read_text())
    access_token = creds.get("access_token", "")
    if not access_token or access_token == "REPLACE_ME":
        raise ValueError("pinterest access_token not configured in credentials")

    return BoardManagerConfig(
        tenant=tenant,
        boards=boards,
        access_token=access_token,
    )
