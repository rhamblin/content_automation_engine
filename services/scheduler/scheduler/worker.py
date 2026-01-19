import asyncio
from uuid import UUID

from common.app_logger import AppLogger
from common.contracts.database_models import Tenant
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
from common.repositories.cross_tenant import TenantRepository
from common.repositories.tenant_scoped import ScheduleRepository


# how can we remove the bases from being imported outside of common....they are not interfaces
class SchedulerWorker:
    """Scheduler Worker"""

    def __init__(self, registry: registry.ProviderRegistry):
        self.logger = self.__get_logger()
        self.registry = registry

    async def work(self) -> None:
        """Main worker loop"""
        self.logger.info("SchedulerWorker started.")
        await asyncio.sleep(5)  # Initial delay before starting scheduling loop
        while True:
            try:
                # get schedule information from DB
                tenants_uuids: list = await self.__getTenantsUUIDsToSchedule()
                for tenant_uuid in tenants_uuids:

                    due_schedules = self.__getDueSchedules(tenant_uuid)
                    tenant_id = str(tenant_uuid)

                    outgoing_msgs = []
                    outgoing_msgs.append(
                        ContentGenerationRequested(
                            tenant_id="",
                            project_id="",
                        )
                    )

                    outgoing_msgs.append(
                        PromotionOrchestratorRequested(tenant_id=tenant_id)
                    )

                    outgoing_msgs.append(CollectAnalyticsRequested(tenant_id=tenant_id))

                    outgoing_msgs.append(ActivityReportRequested(tenant_id=tenant_id))

                    for msg in outgoing_msgs:
                        self.logger.info(f"zzMessage Going for tenant - {tenant_id}!")
                        await self.registry.get_message_broker().publish(msg)
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
            await asyncio.sleep(15)  # Wait before next scheduling cycle

    def __get_logger(self):
        return AppLogger(__name__)

    async def __getDueSchedules(self, tenant_uuid: UUID):
        async with self.registry.get_database().get_session() as session:
            schedule_repository = ScheduleRepository(session, tenant_uuid)

            # need to just get ones that are due
            all_due_schedules = schedule_repository.get_all()

            return all_due_schedules

    async def __getTenantsUUIDsToSchedule(self) -> list[UUID]:
        """
        When tenant count exceeds ~100, refactor to the below
        to keep performance exceptable:
        - Single cross-tenant query for due schedules
        """
        async with self.registry.get_database().get_session() as session:
            tenant_repository = TenantRepository(session)

            all_tenants_uuids: list[Tenant] = await tenant_repository.get_all() or []
            self.logger.info("All Tenants fetched")
        return [tenant.external_id for tenant in all_tenants_uuids]
