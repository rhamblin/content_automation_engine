from typing import TypeVar, List, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Mapped

from common.contracts.interfaces.tenant_scoped_repository import ITenantScopedRepository
from common.repositories.base_repository import BaseRepository


class TenantScoped(Protocol):
    """Protocol for entities that belong to a tenant."""
    tenant_id: Mapped[UUID]


T = TypeVar("T", bound=TenantScoped)


class BaseTenantScopedRepository(ITenantScopedRepository[T], BaseRepository[T]):
    """Base repository for tenant-scoped entities."""

    async def get_all_by_tenant(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[T]:
        stmt = select(self._model).where(self._model.tenant_id == tenant_id).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
