from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class PublicationMetric(Base):
    __tablename__ = "publication_metrics"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_publication_metrics_external_id"),
        UniqueConstraint("publication_id", "snapshot_date", name="uq_publication_metrics_pub_snapshot"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.external_id", ondelete="CASCADE"), nullable=False)
    publication_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("publications.external_id", ondelete="CASCADE"), nullable=False)
    channel_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("channels.external_id", ondelete="CASCADE"), nullable=False)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    publication: Mapped["Publication"] = relationship("Publication", back_populates="publication_metrics")
