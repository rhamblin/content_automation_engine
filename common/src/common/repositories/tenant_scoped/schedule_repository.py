from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Schedule, ScheduleExecution
from common.contracts.database_models.enums import ScheduleExecutionStatus, ScheduleMessageType
from common.repositories._base_tenant_scoped_repository import BaseTenantScopedRepository


class ScheduleRepository(BaseTenantScopedRepository[Schedule]):
    """Repository for Schedule aggregate (includes executions)."""

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

    async def get_by_id_with_executions(self, id: UUID) -> Optional[Schedule]:
        stmt = (
            select(Schedule)
            .options(selectinload(Schedule.schedule_executions))
            .where(Schedule.tenant_id == self._tenant_id, Schedule.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

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

    # Execution methods
    async def add_execution(self, execution: ScheduleExecution) -> ScheduleExecution:
        self._session.add(execution)
        await self._session.flush()
        await self._session.refresh(execution)
        return execution

    async def get_executions(self, schedule_id: UUID, limit: int = 100) -> List[ScheduleExecution]:
        stmt = (
            select(ScheduleExecution)
            .where(
                ScheduleExecution.tenant_id == self._tenant_id,
                ScheduleExecution.schedule_id == schedule_id
            )
            .order_by(ScheduleExecution.started_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_execution_by_id(self, execution_id: UUID) -> Optional[ScheduleExecution]:
        stmt = select(ScheduleExecution).where(
            ScheduleExecution.tenant_id == self._tenant_id,
            ScheduleExecution.id == execution_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_running_executions(self) -> List[ScheduleExecution]:
        stmt = (
            select(ScheduleExecution)
            .where(
                ScheduleExecution.tenant_id == self._tenant_id,
                ScheduleExecution.status == ScheduleExecutionStatus.RUNNING
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_execution_status(
        self,
        execution_id: UUID,
        status: ScheduleExecutionStatus,
        completed_at: Optional[datetime] = None
    ) -> bool:
        execution = await self.get_execution_by_id(execution_id)
        if execution:
            execution.status = status
            if status == ScheduleExecutionStatus.RUNNING and not execution.started_at:
                execution.started_at = datetime.now(timezone.utc)
            if completed_at:
                execution.completed_at = completed_at
            elif status in (ScheduleExecutionStatus.COMPLETED, ScheduleExecutionStatus.FAILED):
                execution.completed_at = datetime.now(timezone.utc)
            await self._session.flush()
            return True
        return False
