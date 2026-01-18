from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Schedule, ScheduleExecution
from common.contracts.database_models.enums import ScheduleExecutionStatus, ScheduleMessageType
from common.repositories.base_tenant_scoped_repository import BaseTenantScopedRepository


class ScheduleRepository(BaseTenantScopedRepository[Schedule]):
    """Repository for Schedule aggregate (includes executions)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Schedule)

    async def add(
        self,
        tenant_id: UUID,
        niche_id: UUID,
        title: str,
        cron_expression: str,
        message_type: ScheduleMessageType = ScheduleMessageType.CONTENT_GENERATION,
        message_payload: Optional[str] = None
    ) -> Schedule:
        schedule = Schedule(
            tenant_id=tenant_id,
            niche_id=niche_id,
            title=title,
            cron_expression=cron_expression,
            message_type=message_type.value,
            message_payload=message_payload
        )
        self._session.add(schedule)
        await self._session.flush()
        await self._session.refresh(schedule)
        return schedule

    async def get_by_id_with_executions(self, id: UUID) -> Optional[Schedule]:
        stmt = (
            select(Schedule)
            .options(selectinload(Schedule.schedule_executions))
            .where(Schedule.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_schedules(self, tenant_id: UUID) -> List[Schedule]:
        stmt = select(Schedule).where(Schedule.tenant_id == tenant_id, Schedule.is_active == True)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_due_schedules(self, before: datetime) -> List[Schedule]:
        stmt = (
            select(Schedule)
            .where(Schedule.is_active == True, Schedule.next_run_at <= before)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_niche(self, niche_id: UUID) -> List[Schedule]:
        stmt = select(Schedule).where(Schedule.niche_id == niche_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_last_run(self, id: UUID, last_run_at: datetime, next_run_at: datetime) -> bool:
        schedule = await self.get_by_id(id)
        if schedule:
            schedule.last_run_at = last_run_at
            schedule.next_run_at = next_run_at
            await self._session.flush()
            return True
        return False

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
            .where(ScheduleExecution.schedule_id == schedule_id)
            .order_by(ScheduleExecution.started_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_execution_by_id(self, execution_id: UUID) -> Optional[ScheduleExecution]:
        return await self._session.get(ScheduleExecution, execution_id)

    async def get_running_executions(self, tenant_id: UUID) -> List[ScheduleExecution]:
        stmt = (
            select(ScheduleExecution)
            .where(
                ScheduleExecution.tenant_id == tenant_id,
                ScheduleExecution.status == ScheduleExecutionStatus.RUNNING.value
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
            execution.status = status.value
            if status == ScheduleExecutionStatus.RUNNING and not execution.started_at:
                execution.started_at = datetime.utcnow()
            if completed_at:
                execution.completed_at = completed_at
            elif status in (ScheduleExecutionStatus.COMPLETED, ScheduleExecutionStatus.FAILED):
                execution.completed_at = datetime.utcnow()
            await self._session.flush()
            return True
        return False
