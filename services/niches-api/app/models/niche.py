from app.models.base import Base
from sqlalchemy import String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import uuid

class Niche(Base):
    __tablename__ = "niches"
    __table_args__ = {"schema": "niches"}

    niche_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    default_budget: Mapped[int] = mapped_column(Integer, nullable=False)

    # ORM-level relationship (does NOT handle deletion)
    keywords: Mapped[List["Keyword"]] = relationship(back_populates="niche")
