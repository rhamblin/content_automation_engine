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


class ITenantScopedRepository(IRepository[T], Generic[T]):
    """Repository interface for tenant-scoped entities."""

    @abstractmethod
    async def get_all_by_tenant(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities for a specific tenant."""
        pass
