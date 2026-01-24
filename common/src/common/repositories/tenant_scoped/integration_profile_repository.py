from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import IntegrationProfile
from common.repositories._base_tenant_scoped_repository import BaseTenantScopedRepository


class IntegrationProfileRepository(BaseTenantScopedRepository[IntegrationProfile]):
    """Repository for IntegrationProfile."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, IntegrationProfile, tenant_id)

    async def add(self, niche_id: UUID, channel_id: UUID) -> IntegrationProfile:
        profile = IntegrationProfile(
            tenant_id=self._tenant_id,
            niche_id=niche_id,
            channel_id=channel_id
        )
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def get_by_id(self, profile_id: UUID) -> Optional[IntegrationProfile]:
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.tenant_id == self._tenant_id,
            IntegrationProfile.external_id == profile_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, include_only_active: bool = True) -> List[IntegrationProfile]:
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.tenant_id == self._tenant_id
        )
        if include_only_active:
            stmt = stmt.where(IntegrationProfile.is_active == True)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_niche_and_channel(
        self, niche_id: UUID, channel_id: UUID
    ) -> Optional[IntegrationProfile]:
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.tenant_id == self._tenant_id,
            IntegrationProfile.niche_id == niche_id,
            IntegrationProfile.channel_id == channel_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate(self, id: UUID) -> bool:
        profile = await self.get_by_id(id)
        if profile:
            profile.is_active = False
            await self._session.flush()
            return True
        return False
