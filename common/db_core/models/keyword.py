from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import String, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.constants import constants

from .base import Base

class Keyword(Base):
    __tablename__ = "keywords"
    __table_args__ = (
        UniqueConstraint('niche_id', 'keyword', name='uq_keyword_per_niche'),
        CheckConstraint("keyword != ''", name='ck_keyword_not_empty'),
        {"schema": "niches"}
    )

    keyword_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    niche_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey(constants.NICHE_ID_FULL_QUALIFIER), nullable=False)
    keyword: Mapped[str] = mapped_column(String, nullable=False)

    niche: Mapped["Niche"] = relationship(back_populates="keywords", lazy="selectin")

    def to_dict(self) -> dict:
        return {
            "keyword_id": str(self.keyword_id),
            "niche_id": str(self.niche_id),
            "keyword": self.keyword,
        }

    def to_readable(self) -> str:
        niche_name = getattr(self.niche, "name", None)
        niche_part = f" (niche='{niche_name}')" if niche_name else ""
        return f"Keyword[{self.keyword_id}]: '{self.keyword}'{niche_part} | niche_id={self.niche_id}"
