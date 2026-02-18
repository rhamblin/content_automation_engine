import uuid as _uuid
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class TenantRole:
    tenant_id: UUID
    role: str


@dataclass(frozen=True)
class AuthContext:
    user_id: UUID
    email: str
    tenant_roles: list[TenantRole] = field(default_factory=list)
    scopes: list[str] = field(default_factory=list)
    identity_provider: str = "azure_entra"
    correlation_id: UUID = field(default_factory=_uuid.uuid4)
