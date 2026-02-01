from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import Keyword
from common.repositories._base_tenant_scoped_repository import (
    BaseTenantScopedRepository,
)


class KeywordRepository(BaseTenantScopedRepository[Keyword]):
    """Repository for Keyword entity."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, Keyword, tenant_id)

    async def add(self, niche_id: UUID, term: str) -> Keyword:
        keyword = Keyword(tenant_id=self._tenant_id, niche_id=niche_id, term=term)
        self._session.add(keyword)
        await self._session.flush()
        await self._session.refresh(keyword)
        return keyword

    async def get_by_niche(
        self, niche_id: UUID, include_only_active: bool = True
    ) -> List[Keyword]:
        stmt = select(Keyword).where(
            Keyword.tenant_id == self._tenant_id, Keyword.niche_id == niche_id
        )
        if include_only_active:
            stmt = stmt.where(Keyword.is_active)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_term(self, niche_id: UUID, term: str) -> Optional[Keyword]:
        stmt = select(Keyword).where(
            Keyword.tenant_id == self._tenant_id,
            Keyword.niche_id == niche_id,
            Keyword.term == term,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate(self, keyword_id: UUID) -> None:
        keyword = await self.get_by_id(keyword_id)
        keyword.is_active = False
        await self._session.flush()

    async def update_term(self, keyword_id: UUID, term: str) -> Keyword:
        keyword = await self.get_by_id(keyword_id)
        keyword.term = term
        await self._session.flush()
        await self._session.refresh(keyword)
        return keyword
