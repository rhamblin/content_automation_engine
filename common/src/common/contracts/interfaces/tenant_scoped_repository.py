from abc import abstractmethod
from typing import TypeVar, Generic, List
from uuid import UUID

from common.contracts.interfaces.repository import IRepository

T = TypeVar("T")


class ITenantScopedRepository(IRepository[T], Generic[T]):
    """Repository interface for tenant-scoped entities."""

    @abstractmethod
    async def get_all_by_tenant(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities for a specific tenant."""
        pass
