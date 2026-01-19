from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Render
from common.contracts.database_models.enums import RenderStatus
from common.repositories._base_tenant_scoped_repository import BaseTenantScopedRepository


class RenderRepository(BaseTenantScopedRepository[Render]):
    """Repository for Render aggregate."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, Render, tenant_id)

    async def add(
        self,
        content_id: UUID,
        niche_id: UUID,
        keyword_id: UUID,
        input_image_id: Optional[UUID] = None,
        style_name: Optional[str] = None
    ) -> Render:
        render = Render(
            tenant_id=self._tenant_id,
            content_id=content_id,
            niche_id=niche_id,
            keyword_id=keyword_id,
            input_image_id=input_image_id,
            style_name=style_name
        )
        self._session.add(render)
        await self._session.flush()
        await self._session.refresh(render)
        return render

    async def get_by_id_with_images(self, id: UUID) -> Optional[Render]:
        stmt = (
            select(Render)
            .options(selectinload(Render.input_image), selectinload(Render.output_image))
            .where(Render.tenant_id == self._tenant_id, Render.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_content(self, content_id: UUID) -> List[Render]:
        stmt = select(Render).where(
            Render.tenant_id == self._tenant_id,
            Render.content_id == content_id
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, status: RenderStatus, limit: int = 100) -> List[Render]:
        stmt = (
            select(Render)
            .where(Render.tenant_id == self._tenant_id, Render.status == status)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending(self, limit: int = 100) -> List[Render]:
        return await self.get_by_status(RenderStatus.PENDING, limit)

    async def get_by_keyword(self, keyword_id: UUID) -> List[Render]:
        stmt = select(Render).where(
            Render.tenant_id == self._tenant_id,
            Render.keyword_id == keyword_id
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, id: UUID, status: RenderStatus) -> bool:
        render = await self.get_by_id(id)
        if render:
            render.status = status
            await self._session.flush()
            return True
        return False
