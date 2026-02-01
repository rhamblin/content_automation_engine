from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.repositories.cross_tenant.channel_repository import ChannelRepository
from common.repositories.tenant_scoped.integration_profile_repository import IntegrationProfileRepository
from common.repositories.tenant_scoped.niche_repository import NicheRepository
from management_api.dependencies import get_db_session
from management_api.schemas.integration_profiles import IntegrationProfileCreate, IntegrationProfileResponse

router = APIRouter(prefix="/tenants/{tenant_id}/integration-profiles", tags=["integration-profiles"])


@router.post("", response_model=IntegrationProfileResponse, status_code=201)
async def create_integration_profile(
    tenant_id: UUID, body: IntegrationProfileCreate, session: AsyncSession = Depends(get_db_session)
):
    # Validate niche exists (tenant-scoped)
    niche_repo = NicheRepository(session, tenant_id)
    await niche_repo.get_by_id(body.niche_id)

    # Validate channel exists
    channel_repo = ChannelRepository(session)
    await channel_repo.get_by_id(body.channel_id)

    repo = IntegrationProfileRepository(session, tenant_id)
    profile = await repo.add(niche_id=body.niche_id, channel_id=body.channel_id)
    await session.commit()
    return profile


@router.get("", response_model=List[IntegrationProfileResponse])
async def list_integration_profiles(tenant_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = IntegrationProfileRepository(session, tenant_id)
    return await repo.get_all(include_only_active=True)


@router.get("/{profile_id}", response_model=IntegrationProfileResponse)
async def get_integration_profile(tenant_id: UUID, profile_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = IntegrationProfileRepository(session, tenant_id)
    return await repo.get_by_id(profile_id)


@router.delete("/{profile_id}", status_code=204)
async def delete_integration_profile(tenant_id: UUID, profile_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = IntegrationProfileRepository(session, tenant_id)
    await repo.deactivate(profile_id)
    await session.commit()
