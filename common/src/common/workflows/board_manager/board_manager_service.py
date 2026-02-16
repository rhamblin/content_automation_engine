"""Board-manager business logic — no file I/O."""

from common.app_logger import AppLogger
from common.providers.distribution_channel.pinterest import PinterestChannel
from common.workflows.board_manager.board_manager_request import BoardItem
from common.workflows.board_manager.board_manager_response import BoardManagerResponse, BoardResult

logger = AppLogger(__name__)


class BoardManagerService:
    """Creates Pinterest boards via the channel provider."""

    def __init__(self, channel: PinterestChannel):
        self.channel = channel

    def create_board(self, item: BoardItem) -> BoardResult:
        """Create a single board."""
        logger.info(f"Creating board: {item.name} ({item.privacy})")
        try:
            result = self.channel.create_board(name=item.name, privacy=item.privacy)
            logger.info(f"  OK: {result['url']}")
            return BoardResult(
                name=item.name,
                board_id=result["board_id"],
                url=result["url"],
            )
        except Exception as e:
            logger.error(f"  FAILED: {item.name} — {e}")
            return BoardResult(name=item.name, error=str(e))

    def create_boards(self, items: list[BoardItem]) -> BoardManagerResponse:
        """Create multiple boards and return aggregate results."""
        response = BoardManagerResponse()
        for i, item in enumerate(items, 1):
            logger.info(f"[{i}/{len(items)}]")
            response.results.append(self.create_board(item))

        logger.info(f"Done — {response.succeeded}/{response.total} succeeded, {response.failed} failed")
        return response
