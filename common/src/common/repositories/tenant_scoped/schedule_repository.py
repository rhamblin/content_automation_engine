from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import Schedule
from common.contracts.database_models.enums import ScheduleMessageType
from common.repositories._base_tenant_scoped_repository import BaseTenantScopedRepository


class ScheduleRepository(BaseTenantScopedRepository[Schedule]):
    """Repository for Schedule."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, Schedule, tenant_id)

    async def add(
        self,
        cron_expression: str,
        message_type: ScheduleMessageType,
        integration_profile_id: Optional[UUID] = None
    ) -> Schedule:
        schedule = Schedule(
            tenant_id=self._tenant_id,
            integration_profile_id=integration_profile_id,
            cron_expression=cron_expression,
            message_type=message_type
        )
        self._session.add(schedule)
        await self._session.flush()
        await self._session.refresh(schedule)
        return schedule

    async def get_active_schedules(self) -> List[Schedule]:
        stmt = select(Schedule).where(Schedule.tenant_id == self._tenant_id, Schedule.is_active)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_integration_profile(self, integration_profile_id: UUID) -> Optional[Schedule]:
        stmt = select(Schedule).where(
            Schedule.tenant_id == self._tenant_id,
            Schedule.integration_profile_id == integration_profile_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_message_type(self, message_type: ScheduleMessageType) -> Optional[Schedule]:
        """Get tenant-level schedule by message type (where integration_profile_id is null)."""
        stmt = select(Schedule).where(
            Schedule.tenant_id == self._tenant_id,
            Schedule.message_type == message_type,
            Schedule.integration_profile_id.is_(None)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate(self, id: UUID) -> bool:
        schedule = await self.get_by_id(id)
        if schedule:
            schedule.is_active = False
            await self._session.flush()
            return True
        return False
