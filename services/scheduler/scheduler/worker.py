import asyncio

from common.app_logger import AppLogger
from common.contracts.messages.activity_report_requested import ActivityReportRequested
from common.contracts.messages.collect_analytics_requested import (
    CollectAnalyticsRequested,
)
from common.contracts.messages.content_generation_requested import (
    ContentGenerationRequested,
)
from common.contracts.messages.promotion_orchestrator_requested import (
    PromotionOrchestratorRequested,
)
from common.providers import registry


class SchedulerWorker:
    """Scheduler Worker"""

    def __init__(self, registry: registry.ProviderRegistry):
        self.logger = self.__get_logger()
        self.registry = registry

    async def work(self) -> None:
        """Main worker loop"""
        self.logger.info("SchedulerWorker started.")
        await asyncio.sleep(10)  # Initial delay before starting scheduling loop
        while True:
            try:
                # get schedule information from DB
                tenants: list = self.__getTenantsToSchedule()

                for tenant in tenants:
                    outgoing_msgs = []
                    outgoing_msgs.append(
                        ContentGenerationRequested(
                            tenant_id="",
                            project_id="",
                        )
                    )

                    outgoing_msgs.append(PromotionOrchestratorRequested(tenant_id=""))

                    outgoing_msgs.append(CollectAnalyticsRequested(tenant_id=""))

                    outgoing_msgs.append(ActivityReportRequested(tenant_id=""))

                    for msg in outgoing_msgs:
                        await self.registry.get_message_broker().publish(msg)
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
            await asyncio.sleep(30)  # Wait before next scheduling cycle

    def __get_logger(self):
        return AppLogger(__name__)

    def __getTenantsToSchedule(self) -> list:
        # placeholder - implement logic to get tenants to schedule from DB
        return []
