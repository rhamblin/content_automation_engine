from __future__ import annotations

from datetime import date
import uuid

from sqlalchemy import Date, Integer, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Metric(Base):
    __tablename__ = "metrics"
    __table_args__ = (
          UniqueConstraint('content_id', 'date', name='uq_metrics_content_date'),  # Ensure one metric entry per content per day
          {"schema": "analytics"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("contents.contents.content_id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    impressions: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    saves: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    content: Mapped["Content"] = relationship("Content", back_populates="metrics")
