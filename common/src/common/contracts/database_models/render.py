from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from .enums import RenderStatus


class Render(Base):
    __tablename__ = "renders"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_renders_external_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.external_id", ondelete="CASCADE"), nullable=False)
    content_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("contents.external_id", ondelete="CASCADE"), nullable=False)
    niche_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("niches.external_id", ondelete="CASCADE"), nullable=False)
    keyword_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("keywords.external_id", ondelete="CASCADE"), nullable=False)
    input_image_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("images.external_id", ondelete="SET NULL"), nullable=True)
    output_image_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("images.external_id", ondelete="SET NULL"), nullable=True)
    style_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[RenderStatus] = mapped_column(String, nullable=False, default=RenderStatus.PENDING.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    content: Mapped["Content"] = relationship("Content", back_populates="renders")
    input_image: Mapped[Optional["Image"]] = relationship("Image", foreign_keys=[input_image_id], back_populates="renders_as_input")
    output_image: Mapped[Optional["Image"]] = relationship("Image", foreign_keys=[output_image_id], back_populates="renders_as_output")
    publications: Mapped[List["Publication"]] = relationship("Publication", back_populates="render", cascade="all, delete", lazy="selectin")
