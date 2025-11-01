from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "identity"}

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    provider_sub: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, nullable=False)

    tenant: Mapped["TenantUser"] = relationship("TenantUser", back_populates="user", cascade="all, delete", lazy="selectin", uselist=False)
