from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from .enums import ScheduleMessageType


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_schedules_external_id"),
        # Tenant-level schedules: one per tenant per message_type
        Index(
            "uq_schedules_tenant_message_type",
            "tenant_id",
            "message_type",
            unique=True,
            postgresql_where=text("integration_profile_id IS NULL"),
        ),
        # Content generation: one per integration_profile
        Index(
            "uq_schedules_integration_profile",
            "integration_profile_id",
            unique=True,
            postgresql_where=text("integration_profile_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    integration_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_profiles.id", ondelete="CASCADE"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cron_expression: Mapped[str] = mapped_column(String, nullable=False)
    message_type: Mapped[ScheduleMessageType] = mapped_column(
        String, nullable=False, default=ScheduleMessageType.CONTENT_GENERATION.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="schedules")
    integration_profile: Mapped[Optional["IntegrationProfile"]] = relationship(
        "IntegrationProfile", back_populates="schedules"
    )
