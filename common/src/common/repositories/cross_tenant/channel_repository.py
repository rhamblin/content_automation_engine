from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import Channel, TenantsChannels
from common.repositories._base_repository import BaseRepository


class ChannelRepository(BaseRepository[Channel]):
    """Repository for Channel aggregate."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Channel)

    async def add(self, identifier: str) -> Channel:
        channel = Channel(identifier=identifier)
        self._session.add(channel)
        await self._session.flush()
        await self._session.refresh(channel)
        return channel

    async def get_by_identifier(self, identifier: str) -> Optional[Channel]:
        stmt = select(Channel).where(Channel.identifier == identifier)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_channels_for_tenant(self, tenant_id: UUID) -> List[Channel]:
        stmt = (
            select(Channel)
            .join(TenantsChannels)
            .where(TenantsChannels.tenant_id == tenant_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_or_create_by_identifier(self, identifier: str) -> Channel:
        existing = await self.get_by_identifier(identifier)
        if existing:
            return existing
        channel = Channel(identifier=identifier)
        return await self.add(channel)
