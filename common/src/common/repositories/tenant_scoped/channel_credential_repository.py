from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import ChannelCredential
from common.repositories._base_tenant_scoped_repository import BaseTenantScopedRepository


class ChannelCredentialRepository(BaseTenantScopedRepository[ChannelCredential]):
    """Repository for ChannelCredential (tenant + channel scoped)."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, ChannelCredential, tenant_id)

    async def upsert(self, channel_id: UUID, credentials: dict) -> ChannelCredential:
        """Insert or update credentials by (tenant, channel)."""
        existing = await self.get_by_channel(channel_id)
        if existing:
            existing.credentials = credentials
            await self._session.flush()
            return existing
        cred = ChannelCredential(
            tenant_id=self._tenant_id,
            channel_id=channel_id,
            credentials=credentials,
        )
        self._session.add(cred)
        await self._session.flush()
        await self._session.refresh(cred)
        return cred

    async def get_by_channel(self, channel_id: UUID) -> Optional[ChannelCredential]:
        stmt = select(ChannelCredential).where(
            ChannelCredential.tenant_id == self._tenant_id,
            ChannelCredential.channel_id == channel_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
