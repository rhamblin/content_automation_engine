from uuid import UUID

import common.contracts.messages as msgs
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger
from common.app_logger import AppLogger
from common.contracts.database_models import Schedule, Tenant
from common.contracts.interfaces import IMessage
from common.providers import registry
from common.repositories.cross_tenant import TenantRepository
from common.repositories.tenant_scoped import ScheduleRepository


class SchedulerWorker:
    """Scheduler Worker"""

    def __init__(self, registry: registry.ProviderRegistry, scheduler: BaseScheduler):
        self.logger = self.__get_logger()
        self.registry = registry
        self.scheduler = scheduler

    async def work(self) -> None:
        """Main worker loop"""
        self.logger.info("SchedulerWorker started.")
        try:
            # get schedule information from DB
            tenants_uuids: list = await self.__getTenantsUUIDsToSchedule()
            self.logger.info(f"Processing {len(tenants_uuids)} tenants for scheduling")
            total_jobs = 0
            for tenant_uuid in tenants_uuids:
                schedules = await self.__getSchedules(tenant_uuid)

                self.logger.info(
                    f"Found {len(schedules)} schedules for tenant {tenant_uuid}"
                )
                for s in schedules:
                    self.logger.info(
                        f"Adding job: schedule_id={s.external_id}, "
                        f"tenant={tenant_uuid}, cron='{s.cron_expression}', "
                        f"message_type={s.message_type}"
                    )
                    self.scheduler.add_job(
                        self.__publish_message,
                        CronTrigger.from_crontab(s.cron_expression),
                        args=[s],
                    )
                    total_jobs += 1
                    self.logger.debug(
                        f"Job added successfully for schedule {s.external_id}"
                    )
            self.logger.info(
                f"SchedulerWorker completed: {total_jobs} jobs added across {len(tenants_uuids)} tenants"
            )
        except Exception as e:
            self.logger.error(f"Worker error: {e}")

    def __get_logger(self):
        return AppLogger(__name__)

    async def __getSchedules(self, tenant_uuid: UUID) -> list[Schedule]:
        async with self.registry.get_database().get_session() as session:
            schedule_repository = ScheduleRepository(session, tenant_uuid)

            all_schedules = await schedule_repository.get_all()

            return all_schedules

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

    async def __publish_message(self, schedule: Schedule):
        self.logger.info(
            f"Executing job: schedule_id={schedule.external_id}, "
            f"tenant={schedule.tenant_id}, message_type={schedule.message_type}"
        )
        message_broker = self.registry.get_message_broker()

        tenant_id = str(schedule.tenant_id)
        message_type = str(schedule.message_type)

        message: IMessage | None = None
        if message_type == msgs.ContentGenerationRequested.topic():
            profile_id = str(schedule.integration_profile_id)
            message = msgs.ContentGenerationRequested(
                tenant_id=tenant_id, project_id=profile_id
            )
        elif message_type == msgs.PromotionOrchestratorRequested.topic():
            message = msgs.PromotionOrchestratorRequested(tenant_id=tenant_id)
        elif message_type == msgs.ActivityReportRequested.topic():
            message = msgs.ActivityReportRequested(tenant_id=tenant_id)
        elif message_type == msgs.CollectAnalyticsRequested.topic():
            message = msgs.CollectAnalyticsRequested(tenant_id=tenant_id)
        else:
            self.logger.error(
                f"An invalid message type {message_type} was found for Schedule {schedule.external_id}"
            )
            return

        if message:
            self.logger.info(
                f"Publishing message: topic={message.topic()}, tenant={tenant_id}, "
                f"schedule_id={schedule.external_id}"
            )
            await message_broker.publish(message)
            self.logger.info(
                f"Message published successfully for schedule {schedule.external_id}"
            )
        else:
            self.logger.error(f"No message created for schedule {schedule.external_id}")
