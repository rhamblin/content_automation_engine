from app.models.base import Base
from app.models.niche import Niche
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

class Keyword(Base):
    __tablename__ = "keywords"
    __table_args__ = {"schema": "niches"}

    keyword_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    niche_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("niches.niches.niche_id"), nullable=False)
    keyword: Mapped[str] = mapped_column(String, nullable=False)

    niche: Mapped[Niche] = relationship(back_populates="keywords")