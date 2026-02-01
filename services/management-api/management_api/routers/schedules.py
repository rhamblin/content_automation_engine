from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models.enums import ScheduleMessageType
from common.repositories.tenant_scoped.integration_profile_repository import IntegrationProfileRepository
from common.repositories.tenant_scoped.schedule_repository import ScheduleRepository
from management_api.dependencies import get_db_session
from management_api.schemas.schedules import ScheduleCreate, ScheduleResponse, ScheduleUpdate

router = APIRouter(prefix="/tenants/{tenant_id}/schedules", tags=["schedules"])


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    tenant_id: UUID, body: ScheduleCreate, session: AsyncSession = Depends(get_db_session)
):
    # Validate integration_profile exists if provided
    if body.integration_profile_id:
        ip_repo = IntegrationProfileRepository(session, tenant_id)
        await ip_repo.get_by_id(body.integration_profile_id)

    repo = ScheduleRepository(session, tenant_id)
    schedule = await repo.add(
        cron_expression=body.cron_expression,
        message_type=ScheduleMessageType(body.message_type),
        integration_profile_id=body.integration_profile_id,
    )
    await session.commit()
    return schedule


@router.get("", response_model=List[ScheduleResponse])
async def list_schedules(tenant_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = ScheduleRepository(session, tenant_id)
    return await repo.get_all(include_only_active=True)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(tenant_id: UUID, schedule_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = ScheduleRepository(session, tenant_id)
    return await repo.get_by_id(schedule_id)


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    tenant_id: UUID, schedule_id: UUID, body: ScheduleUpdate, session: AsyncSession = Depends(get_db_session)
):
    repo = ScheduleRepository(session, tenant_id)
    schedule = await repo.get_by_id(schedule_id)
    if body.cron_expression is not None:
        schedule.cron_expression = body.cron_expression
    if body.is_active is not None:
        schedule.is_active = body.is_active
    await repo.update(schedule)
    await session.commit()
    return schedule


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(tenant_id: UUID, schedule_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = ScheduleRepository(session, tenant_id)
    await repo.deactivate(schedule_id)
    await session.commit()
