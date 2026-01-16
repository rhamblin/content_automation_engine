import asyncio
from common.contracts import PromotionOrchestratorRequested
from common.app_logger import AppLogger
from common.providers import registry


class PromotionOrchestratorWorker:
    """Promotion Orchestrator Worker"""

    def __init__(self, registry: registry.ProviderRegistry):
        self.logger = self.__get_logger()
        self.registry = registry

    async def work(self) -> None:
        """Main worker loop"""
        self.logger.info("PromotionOrchestratorWorker started.")

        while True:
            try:
                incoming_msg: (
                    PromotionOrchestratorRequested
                ) = await self.registry.get_message_broker().consume(
                    PromotionOrchestratorRequested
                )

                if incoming_msg:
                    tenant_id = incoming_msg.tenant_id

                    # do work here to orchestrate promotion

            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

    def __get_logger(self):
        return AppLogger(__name__)
