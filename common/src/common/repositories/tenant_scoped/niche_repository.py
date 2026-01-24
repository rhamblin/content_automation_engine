from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Niche, Keyword
from common.repositories._base_tenant_scoped_repository import BaseTenantScopedRepository


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

    async def get_by_id_with_keywords(self, id: UUID, include_only_active: bool = True) -> Optional[Niche]:
        if include_only_active:
            load_opt = selectinload(Niche.keywords.and_(Keyword.is_active == True))
        else:
            load_opt = selectinload(Niche.keywords)

        stmt = (
            select(Niche)
            .options(load_opt)
            .where(Niche.tenant_id == self._tenant_id, Niche.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_title(self, title: str) -> Optional[Niche]:
        stmt = select(Niche).where(Niche.tenant_id == self._tenant_id, Niche.title == title)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, include_only_active: bool = True) -> List[Niche]:
        stmt = select(Niche).where(Niche.tenant_id == self._tenant_id)
        if include_only_active:
            stmt = stmt.where(Niche.is_active == True)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_keyword(self, keyword: Keyword) -> Keyword:
        self._session.add(keyword)
        await self._session.flush()
        await self._session.refresh(keyword)
        return keyword

    async def get_keywords(self, niche_id: UUID, include_only_active: bool = True) -> List[Keyword]:
        stmt = select(Keyword).where(Keyword.tenant_id == self._tenant_id, Keyword.niche_id == niche_id)
        if include_only_active:
            stmt = stmt.where(Keyword.is_active == True)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_keyword_by_id(self, keyword_id: UUID) -> Optional[Keyword]:
        stmt = select(Keyword).where(Keyword.tenant_id == self._tenant_id, Keyword.id == keyword_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_keyword_by_term(self, niche_id: UUID, term: str) -> Optional[Keyword]:
        stmt = select(Keyword).where(Keyword.tenant_id == self._tenant_id, Keyword.niche_id == niche_id, Keyword.term == term)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate(self, id: UUID) -> bool:
        niche = await self.get_by_id(id)
        if niche:
            niche.is_active = False
            await self._session.flush()
            return True
        return False

    async def deactivate_keyword(self, keyword_id: UUID) -> bool:
        keyword = await self.get_keyword_by_id(keyword_id)
        if keyword:
            keyword.is_active = False
            await self._session.flush()
            return True
        return False
