from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import Image
from common.contracts.database_models.enums import ImageKind
from common.repositories._base_tenant_scoped_repository import BaseTenantScopedRepository


class ImageRepository(BaseTenantScopedRepository[Image]):
    """Repository for Image aggregate."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, Image, tenant_id)

    async def add(
        self,
        niche_id: UUID,
        keyword_id: UUID,
        kind: ImageKind = ImageKind.ORIGINAL
    ) -> Image:
        image = Image(
            tenant_id=self._tenant_id,
            niche_id=niche_id,
            keyword_id=keyword_id,
            kind=kind
        )
        self._session.add(image)
        await self._session.flush()
        await self._session.refresh(image)
        return image

    async def get_by_keyword(self, keyword_id: UUID) -> List[Image]:
        stmt = select(Image).where(
            Image.tenant_id == self._tenant_id,
            Image.keyword_id == keyword_id
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_keyword_and_kind(self, keyword_id: UUID, kind: ImageKind) -> List[Image]:
        stmt = select(Image).where(
            Image.tenant_id == self._tenant_id,
            Image.keyword_id == keyword_id,
            Image.kind == kind
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_niche(self, niche_id: UUID, limit: int = 100, offset: int = 0) -> List[Image]:
        stmt = select(Image).where(
            Image.tenant_id == self._tenant_id,
            Image.niche_id == niche_id
        ).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_kind(self, kind: ImageKind, limit: int = 100) -> List[Image]:
        stmt = select(Image).where(
            Image.tenant_id == self._tenant_id,
            Image.kind == kind
        ).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
