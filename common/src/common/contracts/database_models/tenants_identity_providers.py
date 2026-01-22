from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class TenantsIdentityProviders(Base):
    __tablename__ = "tenants_identity_providers"
    __table_args__ = (
        UniqueConstraint("identity_provider_tenant_id", "tenant_id", name="uq_tenants_identity_providers"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.external_id", ondelete="CASCADE"), primary_key=True)
    identity_provider_tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    identity_provider: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="tenants_identity_providers")
