from __future__ import annotations

import uuid

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TenantUser(Base):
    __tablename__ = "tenant_users"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_tenant_users_user_id"),
        {"schema": "identity"}
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("identity.tenants.tenant_id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("identity.users.user_id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String, nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    user: Mapped["User"] = relationship("User", back_populates="tenant")
