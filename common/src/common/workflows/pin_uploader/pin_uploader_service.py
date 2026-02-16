"""Pin-uploader business logic — no file I/O."""

from common.app_logger import AppLogger
from common.contracts.interfaces.distribution_channel import IDistributionChannel
from common.workflows.pin_uploader.pin_upload_request import PinUploadRequest
from common.workflows.pin_uploader.pin_upload_response import PinResult, PinUploadResponse

logger = AppLogger(__name__)


class PinUploaderService:
    """Uploads pre-built PinItems via a distribution channel."""

    def __init__(self, channel: IDistributionChannel):
        self.channel = channel

    def upload(self, request: PinUploadRequest) -> PinUploadResponse:
        """Upload all pins and return aggregate results."""
        response = PinUploadResponse()

        for i, pin in enumerate(request.pins, 1):
            logger.info(f"[{i}/{len(request.pins)}] Uploading: {pin.title} → board {pin.board_id}")
            try:
                result = self.channel.publish(
                    title=pin.title,
                    description=pin.description,
                    content=pin.image_b64,
                    board_id=pin.board_id,
                    content_type=pin.content_type,
                    link=pin.link,
                    alt_text=pin.alt_text,
                )
                response.results.append(
                    PinResult(
                        board_id=pin.board_id,
                        title=pin.title,
                        pin_id=result.get("post_id"),
                        url=result.get("url"),
                    )
                )
                logger.info(f"  OK: {result.get('url')}")

            except Exception as e:
                logger.error(f"  FAILED: {pin.title} — {e}")
                response.results.append(
                    PinResult(
                        board_id=pin.board_id,
                        title=pin.title,
                        error=str(e),
                    )
                )

        logger.info(f"Done — {response.succeeded}/{response.total} succeeded, {response.failed} failed")
        return response
