from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger
from common.app_logger import AppLogger
from common.contracts.interfaces.message_broker import IMessageBroker
from common.contracts.messages.schedule_updated import ScheduleUpdated


class ScheduleUpdateListener:
    def __init__(
        self, message_broker: IMessageBroker, scheduler: BaseScheduler
    ) -> None:
        self.logger = self.__get_logger()
        self.message_broker = message_broker
        self.scheduler = scheduler

    async def work(self) -> None:
        while True:
            message: ScheduleUpdated = await self.message_broker.consume(
                ScheduleUpdated
            )

            if message is None:
                continue

            tenant_id = message.tenant_id
            schedule_id = message.schedule_id
            cron_expr = message.cron_expression

            self.logger.info(
                f"Schedule Updated message received for tenant {tenant_id} and schedule {schedule_id}"
            )
            self.scheduler.reschedule_job(
                job_id=schedule_id,
                trigger=CronTrigger.from_crontab(cron_expr),
            )

    def __get_logger(self):
        return AppLogger(__name__)
