from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, Integer, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base


class Niche(Base):
    __tablename__ = "niches"
    __table_args__ = (
        UniqueConstraint("name", name="uq_niches_name"),
        UniqueConstraint("domain", name="uq_niches_domain"),
        {"schema": "niches"}
    )

    niche_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    default_budget: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, nullable=False)

    keywords: Mapped[List["Keyword"]] = relationship(back_populates="niche", cascade="all, delete", lazy="selectin")
    integration_profiles: Mapped[List["IntegrationProfile"]] = relationship("IntegrationProfile", back_populates="niche", cascade="all, delete", lazy="selectin")

    def to_dict(self) -> dict:
        return {
            "niche_id": str(self.niche_id),
            "name": self.name,
            "domain": self.domain,
            "default_budget": self.default_budget,
            "keywords": [kw.to_dict() for kw in self.keywords] if self.keywords else [],
            "created_at": self.created_at,
        }

    def to_readable(self) -> str:
        kw_list = ", ".join(kw.keyword for kw in self.keywords) if self.keywords else ""
        return (
            f"Niche[{self.niche_id}]: name='{self.name}', domain='{self.domain}', default_budget={self.default_budget}, created_at='{self.created_at}'"
            f"{', keywords=[' + kw_list + ']' if kw_list else ''}"
        )
