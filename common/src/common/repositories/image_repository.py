from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import Image
from common.contracts.database_models.enums import ImageKind
from common.repositories.base import BaseTenantScopedRepository


class ImageRepository(BaseTenantScopedRepository[Image]):
    """Repository for Image aggregate."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Image)

    async def get_by_keyword(self, keyword_id: UUID) -> List[Image]:
        stmt = select(Image).where(Image.keyword_id == keyword_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_keyword_and_kind(self, keyword_id: UUID, kind: ImageKind) -> List[Image]:
        stmt = select(Image).where(Image.keyword_id == keyword_id, Image.kind == kind.value)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_niche(self, niche_id: UUID, limit: int = 100, offset: int = 0) -> List[Image]:
        stmt = select(Image).where(Image.niche_id == niche_id).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_kind(self, tenant_id: UUID, kind: ImageKind, limit: int = 100) -> List[Image]:
        stmt = select(Image).where(Image.tenant_id == tenant_id, Image.kind == kind.value).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
