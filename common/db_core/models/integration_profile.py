from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from common.constants import constants


from .base import Base
# from


class IntegrationProfile(Base):
    __tablename__ = "integration_profiles"
    __table_args__ = (
        UniqueConstraint(
            'project_id',
            'niche_id',
            'channel_key',
            name='uq_integration_profile_combination'
        ),
        {'schema': 'public'}
    )

    integration_profile_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("identity.projects.project_id", ondelete="CASCADE"), nullable=False)
    niche_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(constants.NICHE_ID_FULL_QUALIFIER, ondelete="CASCADE"), nullable=False)
    channel_key: Mapped[str] = mapped_column(String, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="integration_profiles")
    niche: Mapped["Niche"] = relationship("Niche", back_populates="integration_profiles")
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="integration_profile", lazy="selectin")
