from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Keyword, Niche
from common.repositories._base_tenant_scoped_repository import (
    BaseTenantScopedRepository,
)


class NicheRepository(BaseTenantScopedRepository[Niche]):
    """Repository for Niche aggregate (includes keywords)."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, Niche, tenant_id)

    async def add(self, title: str) -> Niche:
        niche = Niche(tenant_id=self._tenant_id, title=title)
        self._session.add(niche)
        await self._session.flush()
        await self._session.refresh(niche)
        return niche

    async def upsert(
        self,
        title: str,
        brand_name: str | None = None,
        brand_website: str | None = None,
        brand_watermark: str | None = None,
        persona_name: str | None = None,
        persona_prompt: str | None = None,
        channel_prompts: dict | None = None,
    ) -> Niche:
        """Insert or update a niche by (tenant, title)."""
        existing = await self.get_by_title(title)
        if existing:
            existing.brand_name = brand_name
            existing.brand_website = brand_website
            existing.brand_watermark = brand_watermark
            existing.persona_name = persona_name
            existing.persona_prompt = persona_prompt
            existing.channel_prompts = channel_prompts
            existing.is_active = True
            await self._session.flush()
            return existing
        niche = Niche(
            tenant_id=self._tenant_id,
            title=title,
            brand_name=brand_name,
            brand_website=brand_website,
            brand_watermark=brand_watermark,
            persona_name=persona_name,
            persona_prompt=persona_prompt,
            channel_prompts=channel_prompts,
        )
        self._session.add(niche)
        await self._session.flush()
        await self._session.refresh(niche)
        return niche

    async def get_by_id_with_keywords(
        self, id: UUID, include_only_active: bool = True
    ) -> Niche:
        if include_only_active:
            load_opt = selectinload(Niche.keywords.and_(Keyword.is_active))
        else:
            load_opt = selectinload(Niche.keywords)

        stmt = (
            select(Niche)
            .options(load_opt)
            .where(Niche.tenant_id == self._tenant_id, Niche.external_id == id)
        )
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            raise LookupError(f"Niche with id '{id}' not found")
        return entity

    async def get_by_title(self, title: str) -> Optional[Niche]:
        stmt = select(Niche).where(
            Niche.tenant_id == self._tenant_id, Niche.title == title
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, include_only_active: bool = True) -> List[Niche]:
        stmt = select(Niche).where(Niche.tenant_id == self._tenant_id)
        if include_only_active:
            stmt = stmt.where(Niche.is_active)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_keyword(self, keyword: Keyword) -> Keyword:
        self._session.add(keyword)
        await self._session.flush()
        await self._session.refresh(keyword)
        return keyword

    async def get_keywords(
        self, niche_id: UUID, include_only_active: bool = True
    ) -> List[Keyword]:
        stmt = select(Keyword).where(
            Keyword.tenant_id == self._tenant_id, Keyword.niche_id == niche_id
        )
        if include_only_active:
            stmt = stmt.where(Keyword.is_active)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_keyword_by_id(self, keyword_id: UUID) -> Keyword:
        stmt = select(Keyword).where(
            Keyword.tenant_id == self._tenant_id, Keyword.external_id == keyword_id
        )
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            raise LookupError(f"Keyword with id '{keyword_id}' not found")
        return entity

    async def get_keyword_by_term(self, niche_id: UUID, term: str) -> Optional[Keyword]:
        stmt = select(Keyword).where(
            Keyword.tenant_id == self._tenant_id,
            Keyword.niche_id == niche_id,
            Keyword.term == term,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate(self, id: UUID) -> None:
        niche = await self.get_by_id(id)
        niche.is_active = False
        await self._session.flush()

    async def deactivate_keyword(self, keyword_id: UUID) -> None:
        keyword = await self.get_keyword_by_id(keyword_id)
        keyword.is_active = False
        await self._session.flush()
