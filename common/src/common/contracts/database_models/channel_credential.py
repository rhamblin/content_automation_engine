from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import UniqueConstraint, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class ChannelCredential(Base):
    __tablename__ = "channel_credentials"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_channel_credentials_external_id"),
        UniqueConstraint("tenant_id", "channel_id", name="uq_channel_credentials_tenant_channel"),
    )

    external_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.external_id", ondelete="CASCADE"), nullable=False)
    channel_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("channels.external_id", ondelete="CASCADE"), nullable=False)
    credentials: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    channel: Mapped["Channel"] = relationship("Channel")
