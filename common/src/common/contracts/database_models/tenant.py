from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Relationships
    tenants_users: Mapped[List["TenantsUsers"]] = relationship("TenantsUsers", back_populates="tenant", cascade="all, delete", lazy="selectin")
    tenants_identity_providers: Mapped[List["TenantsIdentityProviders"]] = relationship("TenantsIdentityProviders", back_populates="tenant", cascade="all, delete", lazy="selectin")
    tenants_channels: Mapped[List["TenantsChannels"]] = relationship("TenantsChannels", back_populates="tenant", cascade="all, delete", lazy="selectin")
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="tenant", cascade="all, delete", lazy="selectin")
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="tenant", cascade="all, delete", lazy="selectin")
    schedules: Mapped[List["Schedule"]] = relationship("Schedule", back_populates="tenant", cascade="all, delete", lazy="selectin")
    niches: Mapped[List["Niche"]] = relationship("Niche", back_populates="tenant", cascade="all, delete", lazy="selectin")
