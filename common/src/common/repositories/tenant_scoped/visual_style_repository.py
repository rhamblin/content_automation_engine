from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import VisualStyleModel
from common.repositories._base_tenant_scoped_repository import BaseTenantScopedRepository


class VisualStyleRepository(BaseTenantScopedRepository[VisualStyleModel]):
    """Repository for VisualStyleModel (tenant + channel scoped)."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, VisualStyleModel, tenant_id)

    async def upsert(self, channel_id: UUID, name: str, description: str | None, spec: dict) -> VisualStyleModel:
        """Insert or update a style by (tenant, channel, name)."""
        existing = await self.get_by_channel_and_name(channel_id, name)
        if existing:
            existing.description = description
            existing.spec = spec
            existing.is_active = True
            await self._session.flush()
            return existing
        style = VisualStyleModel(
            tenant_id=self._tenant_id,
            channel_id=channel_id,
            name=name,
            description=description,
            spec=spec,
        )
        self._session.add(style)
        await self._session.flush()
        await self._session.refresh(style)
        return style

    async def get_by_channel_and_name(self, channel_id: UUID, name: str) -> Optional[VisualStyleModel]:
        stmt = select(VisualStyleModel).where(
            VisualStyleModel.tenant_id == self._tenant_id,
            VisualStyleModel.channel_id == channel_id,
            VisualStyleModel.name == name,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_channel(self, channel_id: UUID, include_only_active: bool = True) -> List[VisualStyleModel]:
        stmt = select(VisualStyleModel).where(
            VisualStyleModel.tenant_id == self._tenant_id,
            VisualStyleModel.channel_id == channel_id,
        )
        if include_only_active:
            stmt = stmt.where(VisualStyleModel.is_active)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
