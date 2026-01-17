from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Render
from common.contracts.database_models.enums import RenderStatus
from common.repositories.base import BaseTenantScopedRepository


class RenderRepository(BaseTenantScopedRepository[Render]):
    """Repository for Render aggregate."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Render)

    async def get_by_id_with_images(self, id: UUID) -> Optional[Render]:
        stmt = (
            select(Render)
            .options(selectinload(Render.input_image), selectinload(Render.output_image))
            .where(Render.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_content(self, content_id: UUID) -> List[Render]:
        stmt = select(Render).where(Render.content_id == content_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, tenant_id: UUID, status: RenderStatus, limit: int = 100) -> List[Render]:
        stmt = (
            select(Render)
            .where(Render.tenant_id == tenant_id, Render.status == status.value)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending(self, tenant_id: UUID, limit: int = 100) -> List[Render]:
        return await self.get_by_status(tenant_id, RenderStatus.PENDING, limit)

    async def get_by_keyword(self, keyword_id: UUID) -> List[Render]:
        stmt = select(Render).where(Render.keyword_id == keyword_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, id: UUID, status: RenderStatus) -> bool:
        render = await self.get_by_id(id)
        if render:
            render.status = status.value
            await self._session.flush()
            return True
        return False
