from typing import TypeVar, Generic, List
from uuid import UUID

from sqlalchemy import select

from common.contracts.interfaces.tenant_scoped_repository import ITenantScopedRepository
from common.repositories.base import BaseRepository

T = TypeVar("T")


class BaseTenantScopedRepository(ITenantScopedRepository[T], BaseRepository[T], Generic[T]):
    """Base repository for tenant-scoped entities."""

    async def get_all_by_tenant(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[T]:
        stmt = select(self._model).where(self._model.tenant_id == tenant_id).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
