from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Text, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class ContentStatus(enum.Enum):
    DRAFT = "draft"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHED = "published"
    FAILED = "failed"

class Content(Base):
    __tablename__ = "contents"
    __table_args__ = {"schema": "contents"}

    content_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.integration_profiles.integration_profile_id", ondelete="SET NULL"), nullable=True)
    asset_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[List[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    status: Mapped[ContentStatus] = mapped_column(String, nullable=False, default=ContentStatus.DRAFT.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, nullable=False)

    integration_profile: Mapped[Optional["IntegrationProfile"]] = relationship("IntegrationProfile", back_populates="contents")
    publications: Mapped[List["ContentPublication"]] = relationship("ContentPublication", back_populates="content", cascade="all, delete", lazy="selectin")
    metrics: Mapped[List["Metric"]] = relationship("Metric", back_populates="content", cascade="all, delete", lazy="selectin")
