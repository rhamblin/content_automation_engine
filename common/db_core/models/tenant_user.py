from .base import Base
import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tenant import Tenant
    from .user import User

class TenantUser(Base):
    __tablename__ = "tenant_users"
    __table_args__ = {"schema": "identity"}

    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("identity.tenants.tenant_id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("identity.users.user_id"), primary_key=True)
    role: Mapped[str] = mapped_column(String, nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    user: Mapped["User"] = relationship("User", back_populates="tenants")
