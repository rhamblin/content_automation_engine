from dataclasses import dataclass

from ..interfaces.message import IMessage


@dataclass(kw_only=True)
class ScheduleUpdated(IMessage):
    """This topic is used for when an update event is made to Schedules Table."""

    tenant_id: str
    schedule_id: str
    cron_expression: str
