from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Content
from common.repositories.tenant_scoped import BaseTenantScopedRepository


class ContentRepository(BaseTenantScopedRepository[Content]):
    """Repository for Content aggregate."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Content)

    async def add(
        self,
        tenant_id: UUID,
        niche_id: UUID,
        keyword_id: UUID,
        title: str = "[Untitled]",
        description: str = "[No description]"
    ) -> Content:
        content = Content(
            tenant_id=tenant_id,
            niche_id=niche_id,
            keyword_id=keyword_id,
            title=title,
            description=description
        )
        self._session.add(content)
        await self._session.flush()
        await self._session.refresh(content)
        return content

    async def get_by_id_with_renders(self, id: UUID) -> Optional[Content]:
        stmt = (
            select(Content)
            .options(selectinload(Content.renders))
            .where(Content.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_publications(self, id: UUID) -> Optional[Content]:
        stmt = (
            select(Content)
            .options(selectinload(Content.publications))
            .where(Content.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_keyword(self, keyword_id: UUID, limit: int = 100, offset: int = 0) -> List[Content]:
        stmt = select(Content).where(Content.keyword_id == keyword_id).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_niche(self, niche_id: UUID, limit: int = 100, offset: int = 0) -> List[Content]:
        stmt = select(Content).where(Content.niche_id == niche_id).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_title(self, tenant_id: UUID, title_query: str, limit: int = 100) -> List[Content]:
        stmt = (
            select(Content)
            .where(Content.tenant_id == tenant_id, Content.title.ilike(f"%{title_query}%"))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
