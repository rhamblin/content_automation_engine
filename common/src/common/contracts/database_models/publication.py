from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Publication(Base):
    __tablename__ = "publications"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_publications_external_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    render_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("renders.id", ondelete="SET NULL"), nullable=True)
    channel_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    content_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), nullable=False)
    post_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # The ID from channel after posting
    status: Mapped[str] = mapped_column(String, nullable=False)  # ENUM: pending, publishing, published, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    render: Mapped[Optional["Render"]] = relationship("Render", back_populates="publications")
    channel: Mapped["Channel"] = relationship("Channel", back_populates="publications")
    content: Mapped["Content"] = relationship("Content", back_populates="publications")
    promotions: Mapped[List["Promotion"]] = relationship("Promotion", back_populates="publication", cascade="all, delete", lazy="selectin")
    publication_metrics: Mapped[List["PublicationMetric"]] = relationship("PublicationMetric", back_populates="publication", cascade="all, delete", lazy="selectin")
