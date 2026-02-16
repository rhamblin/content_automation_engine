"""Config loader — reads JSON data file, validates boards."""

import json
from dataclasses import dataclass
from pathlib import Path

from common.workflows.board_manager import BoardItem
from common.workflows.board_manager.board_manager_request import VALID_PRIVACY


@dataclass(frozen=True)
class BoardManagerConfig:
    """Validated config from data file."""

    tenant: str
    boards: list[BoardItem]


def load_config(data_file: Path) -> BoardManagerConfig:
    """Load and validate data file."""
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

    return BoardManagerConfig(
        tenant=tenant,
        boards=boards,
    )
