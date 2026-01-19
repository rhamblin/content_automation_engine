from abc import abstractmethod
from typing import TypeVar, List
from uuid import UUID

from common.contracts.interfaces.repository import IRepository

T = TypeVar("T")


class ITenantScopedRepository(IRepository[T]):
    """Repository interface for tenant-scoped entities.

    Implementations must be initialized with a tenant_id and all operations
    are automatically scoped to that tenant.
    """

    @property
    @abstractmethod
    def tenant_id(self) -> UUID:
        """The tenant ID this repository is scoped to."""
        pass
