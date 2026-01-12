from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "identity"}

    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, nullable=False)

    projects: Mapped[List["Project"]] = relationship("Project", back_populates="tenant", cascade="all, delete", lazy="selectin")
    users: Mapped[List["TenantUser"]] = relationship("TenantUser", back_populates="tenant", cascade="all, delete", lazy="selectin")
