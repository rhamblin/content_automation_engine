from typing import List, Optional, Protocol, Type, TypeVar
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped

from common.contracts.interfaces.tenant_scoped_repository import ITenantScopedRepository
from common.repositories.base_repository import BaseRepository, HasExternalId


class TenantScoped(HasExternalId, Protocol):
    """Protocol for entities that belong to a tenant."""

    tenant_id: Mapped[UUID]


T = TypeVar("T", bound=TenantScoped)


class BaseTenantScopedRepository(ITenantScopedRepository[T], BaseRepository[T]):
    """Base repository for tenant-scoped entities.

    All operations are automatically scoped to the tenant_id provided at construction.
    """

    def __init__(self, session: AsyncSession, model: Type[T], tenant_id: UUID):
        super().__init__(session, model)
        self._tenant_id = tenant_id

    @property
    def tenant_id(self) -> UUID:
        return self._tenant_id

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by external ID, scoped to tenant."""
        stmt = select(self._model).where(
            self._model.tenant_id == self._tenant_id, self._model.external_id == id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities for this tenant with pagination."""
        stmt = (
            select(self._model)
            .where(self._model.tenant_id == self._tenant_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, id: UUID) -> None:
        """Delete entity by ID, scoped to tenant."""
        stmt = delete(self._model).where(
            self._model.tenant_id == self._tenant_id, self._model.external_id == id
        )
        await self._session.execute(stmt)
