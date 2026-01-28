from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from .enums import ImageKind


class Image(Base):
    __tablename__ = "images"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_images_external_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.external_id", ondelete="CASCADE"), nullable=False)
    niche_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("niches.external_id", ondelete="CASCADE"), nullable=False)
    keyword_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("keywords.external_id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[ImageKind] = mapped_column(String, nullable=False, default=ImageKind.ORIGINAL.value)
    uri: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    keyword: Mapped["Keyword"] = relationship("Keyword", back_populates="images")
    renders_as_input: Mapped[List["Render"]] = relationship("Render", foreign_keys="[Render.input_image_id]", back_populates="input_image", lazy="selectin")
    renders_as_output: Mapped[List["Render"]] = relationship("Render", foreign_keys="[Render.output_image_id]", back_populates="output_image", lazy="selectin")
