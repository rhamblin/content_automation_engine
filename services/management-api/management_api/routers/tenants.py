from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.repositories.cross_tenant.tenant_repository import TenantRepository
from management_api.dependencies import get_db_session
from management_api.schemas.tenants import (
    TenantChannelCreate,
    TenantChannelResponse,
    TenantCreate,
    TenantResponse,
    TenantUpdate,
    TenantUserCreate,
    TenantUserResponse,
)

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(body: TenantCreate, session: AsyncSession = Depends(get_db_session)):
    repo = TenantRepository(session)
    tenant = await repo.add(title=body.title)
    await session.commit()
    return tenant


@router.get("", response_model=List[TenantResponse])
async def list_tenants(limit: int = 100, offset: int = 0, session: AsyncSession = Depends(get_db_session)):
    repo = TenantRepository(session)
    return await repo.get_all(limit=limit, offset=offset)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = TenantRepository(session)
    return await repo.get_by_id(tenant_id)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: UUID, body: TenantUpdate, session: AsyncSession = Depends(get_db_session)):
    repo = TenantRepository(session)
    tenant = await repo.get_by_id(tenant_id)
    if body.title is not None:
        tenant.title = body.title
    tenant = await repo.update(tenant)
    await session.commit()
    return tenant


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(tenant_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = TenantRepository(session)
    await repo.delete(tenant_id)
    await session.commit()


# --- Tenant-User associations ---

@router.post("/{tenant_id}/users", response_model=TenantUserResponse, status_code=201)
async def add_user_to_tenant(tenant_id: UUID, body: TenantUserCreate, session: AsyncSession = Depends(get_db_session)):
    repo = TenantRepository(session)
    tenant_user = await repo.add_user_to_tenant(tenant_id=tenant_id, user_id=body.user_id, role=body.role)
    await session.commit()
    return tenant_user


@router.delete("/{tenant_id}/users/{user_id}", status_code=204)
async def remove_user_from_tenant(tenant_id: UUID, user_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = TenantRepository(session)
    await repo.remove_user_from_tenant(tenant_id=tenant_id, user_id=user_id)
    await session.commit()


# --- Tenant-Channel associations ---

@router.post("/{tenant_id}/channels", response_model=TenantChannelResponse, status_code=201)
async def add_channel_to_tenant(tenant_id: UUID, body: TenantChannelCreate, session: AsyncSession = Depends(get_db_session)):
    from common.contracts.database_models import TenantsChannels
    repo = TenantRepository(session)
    tc = TenantsChannels(tenant_id=tenant_id, channel_id=body.channel_id)
    tenant_channel = await repo.add_channel_to_tenant(tc)
    await session.commit()
    return tenant_channel


@router.delete("/{tenant_id}/channels/{channel_id}", status_code=204)
async def remove_channel_from_tenant(tenant_id: UUID, channel_id: UUID, session: AsyncSession = Depends(get_db_session)):
    from sqlalchemy import delete as sa_delete
    from common.contracts.database_models import TenantsChannels
    stmt = sa_delete(TenantsChannels).where(
        TenantsChannels.tenant_id == tenant_id,
        TenantsChannels.channel_id == channel_id,
    )
    await session.execute(stmt)
    await session.commit()
