from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class UsersIdentityProviders(Base):
    __tablename__ = "users_identity_providers"
    __table_args__ = (
        UniqueConstraint("identity_provider_user_id", "user_id", name="uq_users_identity_providers"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.external_id", ondelete="CASCADE"), primary_key=True)
    identity_provider_user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    identity_provider: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="users_identity_providers")
