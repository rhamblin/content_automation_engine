from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import ChannelCredential
from common.repositories._base_tenant_scoped_repository import BaseTenantScopedRepository


class ChannelCredentialRepository(BaseTenantScopedRepository[ChannelCredential]):
    """Repository for ChannelCredential (tenant + channel scoped, optionally niche-scoped)."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, ChannelCredential, tenant_id)

    async def upsert(
        self, channel_id: UUID, credentials: dict, niche_id: Optional[UUID] = None
    ) -> ChannelCredential:
        """Insert or update credentials by (tenant, channel, niche)."""
        existing = await self.get_by_channel(channel_id, niche_id=niche_id)
        if existing:
            existing.credentials = credentials
            await self._session.flush()
            return existing
        cred = ChannelCredential(
            tenant_id=self._tenant_id,
            channel_id=channel_id,
            niche_id=niche_id,
            credentials=credentials,
        )
        self._session.add(cred)
        await self._session.flush()
        await self._session.refresh(cred)
        return cred

    async def get_by_channel(
        self, channel_id: UUID, niche_id: Optional[UUID] = None
    ) -> Optional[ChannelCredential]:
        """Get credentials for a (tenant, channel) pair, optionally scoped to a niche."""
        stmt = select(ChannelCredential).where(
            ChannelCredential.tenant_id == self._tenant_id,
            ChannelCredential.channel_id == channel_id,
        )
        if niche_id is not None:
            stmt = stmt.where(ChannelCredential.niche_id == niche_id)
        else:
            stmt = stmt.where(ChannelCredential.niche_id.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_channel_and_niche(
        self, channel_id: UUID, niche_id: UUID
    ) -> Optional[ChannelCredential]:
        """Convenience: get niche-scoped credentials, falling back to tenant-level."""
        niche_cred = await self.get_by_channel(channel_id, niche_id=niche_id)
        if niche_cred:
            return niche_cred
        return await self.get_by_channel(channel_id, niche_id=None)
