from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import String, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_core.models.base import Base


class Niche(Base):
    __tablename__ = "niches"
    __table_args__ = {"schema": "niches"}

    niche_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    default_budget: Mapped[int] = mapped_column(Integer, nullable=False)

    keywords: Mapped[List["Keyword"]] = relationship(back_populates="niche", cascade="all, delete", lazy="selectin")
    integration_profiles: Mapped[List["IntegrationProfile"]] = relationship("IntegrationProfile", back_populates="niche", cascade="all, delete", lazy="selectin")

    def to_dict(self) -> dict:
        return {
            "niche_id": str(self.niche_id),
            "name": self.name,
            "domain": self.domain,
            "default_budget": self.default_budget,
            "keywords": [kw.to_dict() for kw in self.keywords] if self.keywords else [],
        }

    def to_readable(self) -> str:
        kw_list = ", ".join(kw.keyword for kw in self.keywords) if self.keywords else ""
        return (
            f"Niche[{self.niche_id}]: name='{self.name}', domain='{self.domain}', default_budget={self.default_budget}"
            f"{', keywords=[' + kw_list + ']' if kw_list else ''}"
        )
