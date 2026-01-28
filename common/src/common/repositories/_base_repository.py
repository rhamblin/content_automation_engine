from typing import TypeVar, List, Type, Protocol
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped

from common.contracts.interfaces.repository import IRepository


class HasExternalId(Protocol):
    """Protocol for entities with an external ID."""

    external_id: Mapped[UUID]


T = TypeVar("T", bound=HasExternalId)


class BaseRepository(IRepository[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        self._session = session
        self._model = model

    async def get_by_id(self, id: UUID) -> T:
        stmt = select(self._model).where(self._model.external_id == id)
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            raise LookupError(f"{self._model.__name__} with id '{id}' not found")
        return entity

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        stmt = select(self._model).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, entity: T) -> T:
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, id: UUID) -> None:
        stmt = delete(self._model).where(self._model.external_id == id)
        await self._session.execute(stmt)
