from typing import TypeVar, Generic, Optional, List, Type
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.interfaces.repository import IRepository, ITenantScopedRepository

T = TypeVar("T")


class BaseRepository(IRepository[T], Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        self._session = session
        self._model = model

    async def get_by_id(self, id: UUID) -> Optional[T]:
        return await self._session.get(self._model, id)

    async def get_by_external_id(self, external_id: UUID) -> Optional[T]:
        stmt = select(self._model).where(self._model.external_id == external_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        stmt = select(self._model).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, id: UUID) -> bool:
        stmt = delete(self._model).where(self._model.id == id)
        result = await self._session.execute(stmt)
        return result.rowcount > 0


class BaseTenantScopedRepository(ITenantScopedRepository[T], BaseRepository[T], Generic[T]):
    """Base repository for tenant-scoped entities."""

    async def get_all_by_tenant(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[T]:
        stmt = select(self._model).where(self._model.tenant_id == tenant_id).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
