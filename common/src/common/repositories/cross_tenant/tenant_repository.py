from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Tenant, TenantsUsers, TenantsIdentityProviders, TenantsChannels
from common.repositories._base_repository import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for Tenant aggregate."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Tenant)

    async def add(self, title: str) -> Tenant:
        tenant = Tenant(title=title)
        self._session.add(tenant)
        await self._session.flush()
        await self._session.refresh(tenant)
        return tenant

    async def get_by_id_with_users(self, id: UUID) -> Tenant:
        stmt = (
            select(Tenant)
            .options(selectinload(Tenant.tenants_users))
            .where(Tenant.external_id == id)
        )
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            raise LookupError(f"Tenant with id '{id}' not found")
        return entity

    async def get_by_id_with_channels(self, id: UUID) -> Tenant:
        stmt = (
            select(Tenant)
            .options(selectinload(Tenant.tenants_channels))
            .where(Tenant.external_id == id)
        )
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            raise LookupError(f"Tenant with id '{id}' not found")
        return entity

    async def get_by_title(self, title: str) -> Optional[Tenant]:
        stmt = select(Tenant).where(Tenant.title == title)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_user_to_tenant(self, tenant_id: UUID, user_id: UUID, role: str) -> TenantsUsers:
        tenant_user = TenantsUsers(tenant_id=tenant_id, user_id=user_id, role=role)
        self._session.add(tenant_user)
        await self._session.flush()
        return tenant_user

    async def remove_user_from_tenant(self, tenant_id: UUID, user_id: UUID) -> bool:
        stmt = select(TenantsUsers).where(
            TenantsUsers.tenant_id == tenant_id,
            TenantsUsers.user_id == user_id
        )
        result = await self._session.execute(stmt)
        tenant_user = result.scalar_one_or_none()
        if tenant_user:
            await self._session.delete(tenant_user)
            return True
        return False

    async def add_identity_provider(self, provider: TenantsIdentityProviders) -> TenantsIdentityProviders:
        self._session.add(provider)
        await self._session.flush()
        return provider

    async def add_channel_to_tenant(self, tenant_channel: TenantsChannels) -> TenantsChannels:
        self._session.add(tenant_channel)
        await self._session.flush()
        return tenant_channel

    async def get_tenant_channels(self, tenant_id: UUID) -> List[TenantsChannels]:
        stmt = select(TenantsChannels).where(TenantsChannels.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
