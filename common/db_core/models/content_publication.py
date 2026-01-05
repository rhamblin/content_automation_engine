from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class ContentPublication(Base):
    __tablename__ = "content_publications"
    __table_args__ = {"schema": "contents"}

    publication_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("contents.contents.content_id", ondelete="CASCADE"), nullable=False)
    channel_key: Mapped[str] = mapped_column(String, nullable=False)
    platform_post_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, nullable=False)
    platform_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)

    content: Mapped["Content"] = relationship("Content", back_populates="publications")
