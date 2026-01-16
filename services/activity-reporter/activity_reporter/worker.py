import asyncio
from common.contracts import ActivityReportRequested
from common.app_logger import AppLogger
from common.providers import registry


class ActivityReporterWorker:
    """Activity Reporter Worker Description"""

    def __init__(self, registry: registry.ProviderRegistry):
        self.logger = self.__get_logger()
        self.registry = registry

    async def work(self) -> None:
        """Main worker loop - this example processes messages with message type of LocalMessage"""
        self.logger.info("TemplateServiceWorker started.")

        while True:
            try:
                incoming_msg: (
                    ActivityReportRequested
                ) = await self.registry.get_message_broker().consume(
                    ActivityReportRequested
                )

                if incoming_msg:
                    tenant_id = incoming_msg.tenant_id

                    # do work here to generate report

            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

    def __get_logger(self):
        return AppLogger(__name__)
