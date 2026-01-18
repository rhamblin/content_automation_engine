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
            |       +-- ProjectRepository
            |       +-- ReportRepository
            |
            +-- TenantRepository      (global - tenants don't belong to tenants)
            +-- UserRepository        (global - users can belong to multiple tenants)
            +-- ChannelRepository     (global - channels are shared across tenants)
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List
from uuid import UUID

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Base repository interface defining standard CRUD operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by external ID."""
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
    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        pass
