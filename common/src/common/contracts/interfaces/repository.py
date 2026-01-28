"""
Repository pattern class hierarchy:

IRepository[T]                        (Interface - abstract CRUD operations)
    |
    +-- ITenantScopedRepository[T]    (Interface - adds tenant filtering)
    |
    +-- BaseRepository[T]             (Implementation - concrete CRUD with SQLAlchemy)
            |
            +-- BaseTenantScopedRepository[T]   ((Implementation - concrete CRUD with SQLAlchemy and adds tenant filtering)
            |       |
            |       +-- NicheRepository
            |       +-- ContentRepository
            |       +-- ImageRepository
            |       +-- RenderRepository
            |       +-- PublicationRepository
            |       +-- ScheduleRepository
            |       +-- IntegrationProfileRepository
            |       +-- ReportRepository
            |
            +-- TenantRepository      (cross-tenant - tenants don't belong to tenants)
            +-- UserRepository        (cross-tenant - users can belong to multiple tenants)
            +-- ChannelRepository     (cross-tenant - channels are shared across tenants)
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List
from uuid import UUID

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Base repository interface defining standard CRUD operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> T:
        """Get entity by external ID. Raises LookupError if not found."""
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        """Delete entity by ID. Idempotent - no error if not found."""
        pass
