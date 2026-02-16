"""Pinterest Board Manager — orchestrator (all I/O and wiring lives here)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.app_logger import AppLogger
from common.providers.distribution_channel.pinterest import PinterestChannel
from common.workflows.board_manager import BoardManagerService
from pinterest_auth import get_access_token

from config import load_config

logger = AppLogger(__name__)


def main():
    data_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not data_file:
        print("Usage: python -m board-manager data/example.json")
        sys.exit(1)

    # Load + validate config
    config = load_config(data_file)
    logger.info(f"Creating {len(config.boards)} boards (tenant: {config.tenant})")

    # Wire up
    access_token = get_access_token(config.tenant)
    channel = PinterestChannel(access_token=access_token)
    service = BoardManagerService(channel)
    response = service.create_boards(config.boards)

    # Summary
    print(f"\n{'='*50}")
    print(f"Boards created: {response.succeeded}/{response.total}")
    for r in response.results:
        if r.ok:
            print(f"  {r.name} — {r.board_id} ({r.url})")
        else:
            print(f"  {r.name} — FAILED: {r.error}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
