from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Content
from common.repositories._base_tenant_scoped_repository import (
    BaseTenantScopedRepository,
)


class ContentRepository(BaseTenantScopedRepository[Content]):
    """Repository for Content aggregate."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, Content, tenant_id)

    async def add(
        self,
        niche_id: UUID,
        keyword_id: UUID,
        title: str = "[Untitled]",
        description: str = "[No description]",
    ) -> Content:
        content = Content(
            tenant_id=self._tenant_id,
            niche_id=niche_id,
            keyword_id=keyword_id,
            title=title,
            description=description,
        )
        self._session.add(content)
        await self._session.flush()
        await self._session.refresh(content)
        return content

    async def get_by_id_with_renders(self, id: UUID) -> Content:
        stmt = (
            select(Content)
            .options(selectinload(Content.renders))
            .where(Content.tenant_id == self._tenant_id, Content.external_id == id)
        )
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            raise LookupError(f"Content with id '{id}' not found")
        return entity

    async def get_by_id_with_publications(self, id: UUID) -> Content:
        stmt = (
            select(Content)
            .options(selectinload(Content.publications))
            .where(Content.tenant_id == self._tenant_id, Content.external_id == id)
        )
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            raise LookupError(f"Content with id '{id}' not found")
        return entity

    async def get_by_keyword(
        self, keyword_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[Content]:
        stmt = (
            select(Content)
            .where(
                Content.tenant_id == self._tenant_id, Content.keyword_id == keyword_id
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_niche(
        self, niche_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[Content]:
        stmt = (
            select(Content)
            .where(Content.tenant_id == self._tenant_id, Content.niche_id == niche_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_title(
        self, title_query: str, limit: int = 100
    ) -> List[Content]:
        stmt = (
            select(Content)
            .where(
                Content.tenant_id == self._tenant_id,
                Content.title.ilike(f"%{title_query}%"),
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
